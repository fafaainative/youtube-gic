
from datetime import datetime, timezone

from app.modules.trend_radar.tracking_service import (
    TrendTrackingService,
)
from app.modules.trend_radar.schemas import VideoTrend


class FakeRepository:
    def __init__(self):
        self.saved = []
        self.snapshots = []

    def save_snapshot(self, video, observed_at=None):
        self.saved.append((video, observed_at))

    def get_recent_snapshots(self, video_id, limit=3):
        return self.snapshots[:limit]


def make_video():
    return VideoTrend(
        video_id="video123",
        title="Python Tutorial",
        channel_title="Code Channel",
        country_code="NG",
        video_url="https://www.youtube.com/watch?v=video123",
        view_count=10000,
    )


def test_record_observation():
    repository = FakeRepository()
    service = TrendTrackingService(repository=repository)

    video = make_video()

    observed_at = datetime(
        2026,
        11,
        24,
        10,
        0,
        tzinfo=timezone.utc,
    )

    service.record_observation(
        video,
        observed_at=observed_at,
    )

    assert len(repository.saved) == 1
    assert repository.saved[0][0].video_id == "video123"
    assert repository.saved[0][1] == observed_at


def test_analyse_video():
    repository = FakeRepository()

    repository.snapshots = [
        {
            "video_id": "video123",
            "view_count": 16000,
            "observed_at": "2026-11-24T10:00:00+00:00",
        },
        {
            "video_id": "video123",
            "view_count": 10000,
            "observed_at": "2026-11-23T10:00:00+00:00",
        },
        {
            "video_id": "video123",
            "view_count": 5000,
            "observed_at": "2026-11-22T10:00:00+00:00",
        },
    ]

    service = TrendTrackingService(repository=repository)

    result = service.analyse_video("video123")

    assert result["views_delta"] == 6000
    assert result["views_per_day_since_last_snapshot"] == 6000
    assert result["trend_direction"] == "growing"
    assert result["momentum"] == "accelerating"
