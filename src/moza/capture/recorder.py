"""
Segmented Video Recorder with retention management.
Saves video segments organized by timestamp with automatic cleanup of old recordings.
"""

import shutil
import threading
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path

from ..logger import logger


class VideoRecorder:
    """
    Video recorder with automatic segment rotation and retention management.

    Features:
    - Automatic segment rotation based on duration (clock-aligned or interval)
    - Date-based folder partitioning (YYYY-MM-DD)
    - Configurable retention policy (auto-purges expired segments)
    - Multi-codec support (mp4v, avc1, x264)
    - Thread-safe writer lifecycle
    """

    def __init__(
        self,
        base_path: str = "data/recordings",
        segment_duration_minutes: int = 1,
        retention_days: int = 7,
        fps: int = 30,
        codec: str = "mp4v",
        clock_aligned: bool = True
    ):
        self.base_path = Path(base_path)
        self.segment_duration_minutes = segment_duration_minutes
        self.segment_duration = timedelta(minutes=segment_duration_minutes)
        self.retention_days = retention_days
        self.fps = fps
        self.codec = codec
        self.clock_aligned = clock_aligned

        self.writer = None
        self.current_segment_start: Optional[datetime] = None
        self.current_file_path: Optional[Path] = None
        self.frame_size: Optional[Tuple[int, int]] = None
        self.zone_id: str = "default"
        self._lock = threading.Lock()
        self.is_recording = False

        self.base_path.mkdir(parents=True, exist_ok=True)

    def start_recording(self, zone_id: str = "main", frame_size: Optional[Tuple[int, int]] = None) -> None:
        """Start recording session for zone."""
        with self._lock:
            self.zone_id = zone_id
            self.frame_size = frame_size
            self.is_recording = True
            logger.info(f"VideoRecorder started for zone '{zone_id}'")

    def write_frame(self, frame) -> None:
        """Write frame to active or rotated video segment."""
        if not self.is_recording:
            return


        with self._lock:
            now = datetime.now()

            # Determine if new segment is needed
            need_new_segment = (
                self.writer is None or
                self.current_segment_start is None or
                (now - self.current_segment_start) >= self.segment_duration
            )

            if need_new_segment:
                self._rotate_segment(now, frame.shape)

            if self.writer is not None:
                self.writer.write(frame)

    def _rotate_segment(self, timestamp: datetime, frame_shape: tuple) -> None:
        """Close current segment and open a new segment file."""
        import cv2

        if self.writer is not None:
            self.writer.release()
            self.writer = None
            logger.debug(f"Segment finalized: {self.current_file_path}")

        # Folder per date: data/recordings/YYYY-MM-DD/
        date_folder = self.base_path / timestamp.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        # Filename: zone_HH-MM-SS.mp4
        filename = f"{self.zone_id}_{timestamp.strftime('%H-%M-%S')}.mp4"
        self.current_file_path = date_folder / filename
        self.current_segment_start = timestamp

        h, w = frame_shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.writer = cv2.VideoWriter(str(self.current_file_path), fourcc, self.fps, (w, h))

        if not self.writer.isOpened():
            logger.error(f"Failed to open VideoWriter for {self.current_file_path}")
            self.writer = None
        else:
            logger.info(f"New video segment started: {self.current_file_path}")

        # Periodically enforce retention cleanup
        self._enforce_retention()

    def _enforce_retention(self) -> None:
        """Delete folders older than retention_days."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        try:
            for item in self.base_path.iterdir():
                if item.is_dir():
                    try:
                        folder_date = datetime.strptime(item.name, "%Y-%m-%d")
                        if folder_date < cutoff_date:
                            logger.info(f"Purging expired recording folder: {item}")
                            shutil.rmtree(item)
                    except ValueError:
                        pass
        except Exception as e:
            logger.warning(f"Retention cleanup error: {e}")

    def stop_recording(self) -> None:
        """Finalize and close active recording."""
        with self._lock:
            self.is_recording = False
            if self.writer is not None:
                self.writer.release()
                self.writer = None
                logger.info(f"Recording stopped. Last file: {self.current_file_path}")
