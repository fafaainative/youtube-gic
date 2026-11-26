
from datetime import datetime, timedelta, timezone

from app.storage.snapshots import SnapshotRepository
from app.modules.trend_radar.trend_analysis import (
    analyze_video_trend,
    parse_timestamp,
)


DEFAULT_MIN_COLLECTION_INTERVAL = timedelta(minutes=60)


def _as_utc(value):
    """Convert a supported timestamp value to UTC."""

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        return parse_timestamp(value)

    return None


def resolve_observation_time(observed_at=None):
    """Resolve the observation time used for collection decisions."""

    if observed_at is None:
        return datetime.now(timezone.utc)

    return _as_utc(observed_at)


def should_record_snapshot(
    latest_snapshot,
    observed_at,
    min_interval=DEFAULT_MIN_COLLECTION_INTERVAL,
):
    """Decide whether an observation may be recorded."""

    observation_time = _as_utc(observed_at)

    if observation_time is None:
        return False

    if not latest_snapshot:
        return True

    latest_time = _as_utc(
        latest_snapshot.get("observed_at")
    )

    if latest_time is None or observation_time <= latest_time:
        return False

    return (
        observation_time - latest_time >= min_interval
    )


class TrendTrackingService:
    """Manage historical observations and analyse video trends."""

    def __init__(
        self,
        repository=None,
        min_collection_interval=None,
    ):
        self.repository = repository or SnapshotRepository()
        self.min_collection_interval = (
            min_collection_interval
            if min_collection_interval is not None
            else DEFAULT_MIN_COLLECTION_INTERVAL
        )

    def record_observation(self, video, observed_at=None):
        """Record an observation when the cooldown allows it."""

        observation_time = resolve_observation_time(
            observed_at
        )

        if observation_time is None:
            return False

        snapshots = self.repository.get_recent_snapshots(
            video_id=video.video_id,
            limit=1,
        )
        latest_snapshot = snapshots[0] if snapshots else None

        if not should_record_snapshot(
            latest_snapshot=latest_snapshot,
            observed_at=observation_time,
            min_interval=self.min_collection_interval,
        ):
            return False

        self.repository.save_snapshot(
            video,
            observed_at=observation_time,
        )

        return True

    def analyse_video(self, video_id):
        """Analyse the latest observations for one video."""

        snapshots = self.repository.get_recent_snapshots(
            video_id=video_id,
            limit=3,
        )

        return analyze_video_trend(snapshots)

    def record_and_analyse(self, video, observed_at=None):
        """
        Record an observation if allowed, then analyse history.
        """

        self.record_observation(
            video=video,
            observed_at=observed_at,
        )

        return self.analyse_video(video.video_id)
