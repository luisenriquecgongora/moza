"""
Real-time analytics processor with sliding window aggregations.
Stores detection metrics in SQLite database for analysis and decision-making.
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

from ..logger import logger


class AnalyticsEngine:
    """
    Real-time analytics processor with sliding window aggregations.
    Derives actionable metrics from raw detections and persists time-series history.
    """

    def __init__(self, db_path: str = "data/metrics.db", window_minutes: int = 5):
        self.db_path = db_path
        self.window = timedelta(minutes=window_minutes)

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.success(f"AnalyticsEngine initialized (db={self.db_path}, window={window_minutes}m)")

    @contextmanager
    def _get_connection(self):
        """Context manager that guarantees connection is closed on exit."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema with migration safeguards."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    zone_id TEXT NOT NULL,
                    person_count INTEGER NOT NULL,
                    bounding_boxes TEXT,
                    behaviors TEXT,
                    session_id TEXT,
                    bottle_count INTEGER DEFAULT 0,
                    cup_count INTEGER DEFAULT 0,
                    wine_glass_count INTEGER DEFAULT 0,
                    total_beverages INTEGER DEFAULT 0,
                    knife_count INTEGER DEFAULT 0,
                    total_hazards INTEGER DEFAULT 0,
                    phone_count INTEGER DEFAULT 0,
                    broken_glass_detected INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_zone_time ON detections(zone_id, timestamp)")
            conn.commit()

    def log_detection(
        self,
        zone_id: str,
        person_count: int,
        bounding_boxes: Optional[List] = None,
        behaviors: Optional[Dict] = None,
        session_id: Optional[str] = None,
        object_counts: Optional[Dict[str, int]] = None,
        broken_glass: bool = False
    ) -> None:
        """Log a detection event into SQLite time-series table."""
        counts = object_counts or {}
        bottle_c = counts.get("bottle", 0)
        cup_c = counts.get("cup", 0)
        wine_glass_c = counts.get("wine glass", 0) + counts.get("cocktail_glass", 0)
        total_bev = bottle_c + cup_c + wine_glass_c
        knife_c = counts.get("knife", 0)
        hazards_c = knife_c + (1 if broken_glass else 0)
        phone_c = counts.get("cell phone", 0)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO detections (
                    zone_id, person_count, bounding_boxes, behaviors, session_id,
                    bottle_count, cup_count, wine_glass_count, total_beverages,
                    knife_count, total_hazards, phone_count, broken_glass_detected
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                zone_id,
                person_count,
                json.dumps(bounding_boxes or []),
                json.dumps(behaviors or {}),
                session_id,
                bottle_c,
                cup_c,
                wine_glass_c,
                total_bev,
                knife_c,
                hazards_c,
                phone_c,
                1 if broken_glass else 0
            ))
            conn.commit()

    def get_current_metrics(self, zone_id: str) -> Dict[str, Any]:
        """
        Derive sliding-window metrics for a zone over the configured window.
        """
        cutoff = (datetime.now() - self.window).strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            # Current count (latest reading)
            cursor = conn.execute("""
                SELECT person_count, bottle_count, cup_count, wine_glass_count,
                       total_beverages, knife_count, total_hazards, broken_glass_detected
                FROM detections
                WHERE zone_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (zone_id,))
            row = cursor.fetchone()

            if not row:
                return {
                    "current_count": 0,
                    "avg_count": 0.0,
                    "max_count": 0,
                    "min_count": 0,
                    "trend": "stable",
                    "total_beverages": 0,
                    "bottle_count": 0,
                    "wine_glass_count": 0,
                    "cup_count": 0,
                    "knife_count": 0,
                    "total_hazards": 0,
                    "broken_glass_detected": False
                }

            current_count = row["person_count"]
            tot_bev = row["total_beverages"]
            knife_c = row["knife_count"]
            tot_haz = row["total_hazards"]
            broken_g = bool(row["broken_glass_detected"])

            # Window metrics
            cursor = conn.execute("""
                SELECT AVG(person_count) as avg_p, MAX(person_count) as max_p, MIN(person_count) as min_p
                FROM detections
                WHERE zone_id = ? AND timestamp >= ?
            """, (zone_id, cutoff))
            stats = cursor.fetchone()

            avg_p = float(stats["avg_p"]) if stats and stats["avg_p"] is not None else float(current_count)
            max_p = int(stats["max_p"]) if stats and stats["max_p"] is not None else current_count
            min_p = int(stats["min_p"]) if stats and stats["min_p"] is not None else current_count

            # Trend estimation: compare first half of window vs second half
            mid_cutoff = (datetime.now() - (self.window / 2)).strftime("%Y-%m-%d %H:%M:%S")
            c1 = conn.execute("SELECT AVG(person_count) as a FROM detections WHERE zone_id = ? AND timestamp >= ? AND timestamp < ?",
                              (zone_id, cutoff, mid_cutoff)).fetchone()
            c2 = conn.execute("SELECT AVG(person_count) as a FROM detections WHERE zone_id = ? AND timestamp >= ?",
                              (zone_id, mid_cutoff)).fetchone()

            trend = "stable"
            if c1 and c2 and c1["a"] is not None and c2["a"] is not None:
                diff = c2["a"] - c1["a"]
                if diff > 1.5:
                    trend = "increasing"
                elif diff < -1.5:
                    trend = "decreasing"

            return {
                "current_count": current_count,
                "avg_count": avg_p,
                "max_count": max_p,
                "min_count": min_p,
                "trend": trend,
                "total_beverages": tot_bev,
                "bottle_count": row["bottle_count"],
                "wine_glass_count": row["wine_glass_count"],
                "cup_count": row["cup_count"],
                "knife_count": knife_c,
                "total_hazards": tot_haz,
                "broken_glass_detected": broken_g
            }
