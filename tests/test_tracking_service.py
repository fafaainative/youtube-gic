from app.modules.trend_radar.tracking_service import TrendTrackingService
from app.storage.snapshots import SnapshotRepository
from app.modules.trend_radar.schemas import VideoTrend
from datetime import datetime, timezone


def test_record_and_analyse(tmp_path):
    database_path = tmp_path / "test_tracking.db"

    repository = SnapshotRepository(database_path=database_path)

    tracking_service = TrendTrackingService(repository=repository)

    video = VideoTrend(
        video_id="video_123",
        title="Test Video",
        channel_title="Test Channel",
        published_at="2026-11-20T10:00:00Z",
        country_code="NG",
        video_url="https://www.youtube.com/watch?v=video_123",
        view_count=1000,
        like_count=100,
        comment_count=10,
    )

    result = tracking_service.record_and_analyse(
        video=video,
        observed_at=datetime(2026, 11, 25, 10, 0, 0, tzinfo=timezone.utc),
    )

    assert result["trend_direction"] == "new"

    assert repository.get_snapshot_count("video_123") == 1
