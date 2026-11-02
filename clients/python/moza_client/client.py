"""
Featherweight Moza Client.
Communicates with the standalone Moza server daemon via HTTP or WebSocket.
Has ZERO heavy ML/CV dependencies (requires only standard Python libraries).
"""

from dataclasses import dataclass
from typing import Optional, Callable
import json
import urllib.request
import threading
import time


@dataclass
class MozaTelemetry:
    """Telemetry frame received from Moza server."""
    status: str
    people_count: int
    bottle_count: int
    wine_glass_count: int
    total_beverages: int
    knife_count: int
    total_hazards: int
    broken_glass: bool
    trend: str
    timestamp: float


class MozaClient:
    """
    Featherweight client for Takient Robot Host and edge devices.
    Connects to local or remote Moza vision daemon.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8100, timeout: float = 2.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self._streaming = False
        self._stream_thread: Optional[threading.Thread] = None
        self._on_telemetry_callback: Optional[Callable[[MozaTelemetry], None]] = None

    def is_available(self) -> bool:
        """Check if Moza server is running and reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/health")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("status") == "healthy"
        except Exception:
            return False

    def get_current_metrics(self) -> Optional[MozaTelemetry]:
        """Fetch latest detection metrics via HTTP GET."""
        try:
            req = urllib.request.Request(f"{self.base_url}/metrics/current")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return MozaTelemetry(
                    status=data.get("status", "unknown"),
                    people_count=data.get("people_count", 0),
                    bottle_count=data.get("bottle_count", 0),
                    wine_glass_count=data.get("wine_glass_count", 0),
                    total_beverages=data.get("total_beverages", 0),
                    knife_count=data.get("knife_count", 0),
                    total_hazards=data.get("total_hazards", 0),
                    broken_glass=bool(data.get("broken_glass", False)),
                    trend=data.get("trend", "stable"),
                    timestamp=data.get("timestamp", time.time())
                )
        except Exception:
            return None

    def start_polling(self, interval_seconds: float = 1.0, callback: Optional[Callable[[MozaTelemetry], None]] = None) -> None:
        """Start background polling thread to receive continuous telemetry."""
        if self._streaming:
            return

        self._on_telemetry_callback = callback
        self._streaming = True

        def poll_loop():
            while self._streaming:
                telemetry = self.get_current_metrics()
                if telemetry and self._on_telemetry_callback:
                    try:
                        self._on_telemetry_callback(telemetry)
                    except Exception:
                        pass
                time.sleep(interval_seconds)

        self._stream_thread = threading.Thread(target=poll_loop, daemon=True)
        self._stream_thread.start()

    def stop_polling(self) -> None:
        """Stop background telemetry thread."""
        self._streaming = False
        if self._stream_thread:
            self._stream_thread.join(timeout=2.0)
            self._stream_thread = None
