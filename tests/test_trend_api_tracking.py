
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class FakeTrackingService:
    def __init__(self):
        self.recorded_video_ids = []

        self.repository = self

    def record_and_analyse(self, video):
        self.recorded_video_ids.append(video.video_id)

        return {
            "previous_view_count": None,
            "views_delta": None,
            "interval_days": None,
            "views_per_day_since_last_snapshot": None,
            "views_growth_percent": None,
            "trend_direction": "new",
            "previous_interval_views_per_day": None,
            "views_per_day_change": None,
            "momentum": "insufficient_history",
        }

    def get_recent_snapshots(self, video_id, limit=30):
        return [
            {
                "video_id": video_id,
                "view_count": 1000,
                "observed_at": "2026-11-24T10:00:00+00:00",
            }
        ]

    def analyse_video(self, video_id):
        return {
            "trend_direction": "new",
            "views_delta": None,
            "momentum": "insufficient_history",
        }


def test_trends_api_records_video_observations(monkeypatch):
    fake_tracking = FakeTrackingService()

    monkeypatch.setattr(
        "app.main.trend_tracking_service",
        fake_tracking,
    )

    monkeypatch.setattr(
        "app.main.get_youtube_api_key",
        lambda: "test-key",
    )

    class FakeYouTubeClient:
        def get_most_popular_videos(
            self,
            region_code,
            max_results=10,
            category_id=None,
        ):
            return [
                {
                    "id": "video123",
                    "snippet": {
                        "title": "Python Tutorial",
                        "channelTitle": "Code Channel",
                        "publishedAt": "2026-11-23T10:00:00Z",
                    },
                    "statistics": {
                        "viewCount": "10000",
                        "likeCount": "500",
                        "commentCount": "100",
                    },
                }
            ]

    monkeypatch.setattr(
        "app.main.YouTubeDataClient",
        lambda api_key: FakeYouTubeClient(),
    )

    response = client.get("/api/v1/trends?region=NG")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["video_id"] == "video123"
    assert data[0]["trend_direction"] == "new"

    assert fake_tracking.recorded_video_ids == ["video123"]


def test_video_history_endpoint(monkeypatch):
    fake_tracking = FakeTrackingService()

    monkeypatch.setattr(
        "app.main.trend_tracking_service",
        fake_tracking,
    )

    response = client.get(
        "/api/v1/trends/video123/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["video_id"] == "video123"
    assert data["snapshot_count"] == 1
    assert data["trend_analysis"]["trend_direction"] == "new"
