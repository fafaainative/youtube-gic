
from app.storage.snapshots import SnapshotRepository
from app.modules.trend_radar.trend_analysis import (
    analyze_video_trend,
)


class TrendTrackingService:
    """Manage historical observations and analyse video trends."""

    def __init__(self, repository=None):
        self.repository = repository or SnapshotRepository()

    def record_observation(self, video, observed_at=None):
        """Save the current video observation."""

        self.repository.save_snapshot(
            video,
            observed_at=observed_at,
        )

    def analyse_video(self, video_id):
        """Analyse the latest observations for one video."""

        snapshots = self.repository.get_recent_snapshots(
            video_id=video_id,
            limit=3,
        )

        return analyze_video_trend(snapshots)

    def record_and_analyse(self, video, observed_at=None):
        """
        Record a new observation, then analyse its history.
        """

        self.record_observation(
            video=video,
            observed_at=observed_at,
        )

        return self.analyse_video(video.video_id)
