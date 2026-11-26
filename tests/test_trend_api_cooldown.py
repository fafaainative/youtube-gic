from fastapi.testclient import TestClient

from app.main import app
from app.modules.trend_radar.tracking_service import TrendTrackingService
from app.storage.snapshots import SnapshotRepository


client = TestClient(app)


def test_repeated_trend_requests_respect_cooldown(monkeypatch, tmp_path):
    repository = SnapshotRepository(
        database_path=tmp_path / "api_cooldown.db"
    )
    tracking_service = TrendTrackingService(repository=repository)

    monkeypatch.setattr(
        "app.main.trend_tracking_service",
        tracking_service,
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
                        "viewCount": "1000",
                        "likeCount": "100",
                        "commentCount": "10",
                    },
                }
            ]

    monkeypatch.setattr(
        "app.main.YouTubeDataClient",
        lambda api_key: FakeYouTubeClient(),
    )

    first_response = client.get("/api/v1/trends?region=NG")
    second_response = client.get("/api/v1/trends?region=NG")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert repository.get_snapshot_count("video123") == 1
    assert (
        second_response.json()[0]["trend_direction"] == "new"
    )

    history_response = client.get(
        "/api/v1/trends/video123/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert history["snapshot_count"] == 1
    assert history["trend_analysis"]["trend_direction"] == "new"
