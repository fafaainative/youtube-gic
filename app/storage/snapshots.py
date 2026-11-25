import sqlite3
from pathlib import Path
from datetime import datetime, timezone


DEFAULT_DATABASE_PATH = Path("data/trend_snapshots.db")


class SnapshotRepository:
    """Persist and retrieve historical YouTube video observations."""

    def __init__(self, database_path=DEFAULT_DATABASE_PATH):
        self.database_path = Path(database_path)

        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize_database()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS video_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    region_code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    channel_title TEXT NOT NULL,
                    published_at TEXT,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_video_snapshots_video_time
                ON video_snapshots(video_id, observed_at)
                """
            )

    def save_snapshot(self, video, observed_at=None):
        """Store one historical observation."""

        timestamp = observed_at or datetime.now(timezone.utc)

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        timestamp_text = timestamp.isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO video_snapshots (
                    video_id,
                    observed_at,
                    region_code,
                    title,
                    channel_title,
                    published_at,
                    view_count,
                    like_count,
                    comment_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    video.video_id,
                    timestamp_text,
                    video.country_code,
                    video.title,
                    video.channel_title,
                    video.published_at,
                    video.view_count,
                    video.like_count,
                    video.comment_count,
                ),
            )

    def get_previous_snapshot(
        self,
        video_id,
        before_timestamp,
    ):
        """Return the latest observation before a timestamp."""
        
        if before_timestamp.tzinfo is None:
            before_timestamp = before_timestamp.replace(
                tzinfo=timezone.utc
            )
        else:
            before_timestamp = before_timestamp.astimezone(
                timezone.utc
            )

        before_text = before_timestamp.isoformat()

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute(
                """
                SELECT *
                FROM video_snapshots
                WHERE video_id = ?
                  AND observed_at < ?
                ORDER BY observed_at DESC
                LIMIT 1
                """,
                (video_id, before_text),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_recent_snapshots(
        self,
        video_id,
        limit=3,
    ):
        """Return the most recent snapshots, newest first."""

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT *
                FROM video_snapshots
                WHERE video_id = ?
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (video_id, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_snapshot_count(self, video_id):
        """Return the number of observations for one video."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM video_snapshots
                WHERE video_id = ?
                """,
                (video_id,),
            ).fetchone()

        return row[0]
