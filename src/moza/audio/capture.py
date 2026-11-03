"""
Audio capture module for ambient sound level metering and fracture acoustic analysis.
"""

import threading
import queue
from typing import Optional
import numpy as np

from ..logger import logger

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class AudioCapture:
    """
    Background audio recorder for sound level monitoring and acoustic fracture detection.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        chunk_size: int = 1024,
        channels: int = 1,
        device_index: Optional[int] = None
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        self.is_running = False
        self.audio_queue = queue.Queue(maxsize=10)
        self._thread: Optional[threading.Thread] = None
        self._pyaudio = None
        self._stream = None

    def start(self) -> None:
        """Start background microphone recording."""
        if not PYAUDIO_AVAILABLE:
            logger.warning("PyAudio not installed; acoustic analysis disabled.")
            return

        if self.is_running:
            return

        try:
            self._pyaudio = pyaudio.PyAudio()
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            self.is_running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            logger.info(f"AudioCapture started @ {self.sample_rate}Hz")
        except Exception as e:
            logger.error(f"Failed to open audio input: {e}")

    def _capture_loop(self) -> None:
        while self.is_running and self._stream:
            try:
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                if self.audio_queue.full():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.audio_queue.put_nowait(samples)
            except Exception:
                break

    def get_latest_chunk(self) -> Optional[np.ndarray]:
        """Retrieve most recent audio chunk."""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def calculate_db(self, samples: np.ndarray) -> float:
        """Calculate RMS decibel level."""
        if samples is None or len(samples) == 0:
            return 0.0
        rms = np.sqrt(np.mean(samples ** 2))
        if rms <= 1e-7:
            return 0.0
        return float(20.0 * np.log10(rms) + 90.0)  # Calibrated venue scale

    def stop(self) -> None:
        """Stop audio stream."""
        self.is_running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None
