"""
Occupancy Reporter - Buffers per-second people counts and posts to API every minute.
Collects people and beverage detection counts and batches them into minute records.
"""

import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any


class OccupancyReporter:
    """
    Buffers per-second occupancy readings and posts them to backend API every minute.
    """

    def __init__(self, api_client: Any, room_id: str, business_id: str):
        self.api_client = api_client
        self.room_id = room_id
        self.business_id = business_id

        self._buffer: List[Dict[str, Any]] = []
        self._current_minute: Optional[datetime] = None
        self._lock = threading.Lock()

        self._running = False
        self._flush_thread: Optional[threading.Thread] = None

        self._total_readings = 0
        self._total_flushes = 0
        self._failed_flushes = 0

    def start(self) -> None:
        """Start background minute-flush thread."""
        if self._running:
            return
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def stop(self) -> None:
        """Stop reporter and flush remaining data."""
        if not self._running:
            return
        self._running = False
        self._flush()
        if self._flush_thread:
            self._flush_thread.join(timeout=3.0)

    def record(self, count: int, bottle_count: int = 0, cup_count: int = 0, audio_level: Optional[float] = None) -> None:
        """Record detection reading for current second."""
        now = datetime.now()
        second = now.second
        minute_start = now.replace(second=0, microsecond=0)

        with self._lock:
            if self._current_minute is not None and minute_start > self._current_minute:
                self._flush_locked()
                self._current_minute = minute_start
            elif self._current_minute is None:
                self._current_minute = minute_start

            self._buffer.append({
                "second": second,
                "count": max(0, count),
                "bottleCount": max(0, bottle_count),
                "cupCount": max(0, cup_count),
                "audioLevel": audio_level
            })
            self._total_readings += 1

    def _flush_loop(self) -> None:
        while self._running:
            time.sleep(1.0)
            now = datetime.now()
            with self._lock:
                if self._current_minute and now >= self._current_minute.replace(second=59, microsecond=999999):
                    self._flush_locked()

    def _flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        if not self._buffer or not self._current_minute:
            return

        minute_iso = self._current_minute.isoformat()
        readings_copy = list(self._buffer)
        self._buffer.clear()
        self._current_minute = None

        payload = {
            "roomId": self.room_id,
            "businessId": self.business_id,
            "minute": minute_iso,
            "readings": readings_copy
        }

        # Dispatch async to avoid holding lock
        threading.Thread(target=self._send_payload, args=(payload,), daemon=True).start()

    def _send_payload(self, payload: Dict[str, Any]) -> None:
        try:
            if self.api_client and hasattr(self.api_client, "post"):
                self.api_client.post("/client/occupancy", payload)
                self._total_flushes += 1
        except Exception:
            self._failed_flushes += 1
