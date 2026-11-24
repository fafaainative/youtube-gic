
import httpx
import pytest
from fastapi.testclient import TestClient
from app.modules.trend_radar.service import get_country_trends

from app.main import app
from app.config import get_youtube_api_key
from app.integrations.youtube_client import (
    YouTubeAPIError,
    YouTubeDataClient,
)


client = TestClient(app)


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
                    "title": "Python for Beginners",
                    "channelTitle": "Code Academy",
                    "publishedAt": "2026-11-20T10:00:00Z",
                },
                "statistics": {
                    "viewCount": "12000",
                    "likeCount": "900",
                    "commentCount": "120",
                },
            }
        ]


def test_country_trends_returns_structured_videos(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_youtube_api_key",
        lambda: "test-key",
    )

    monkeypatch.setattr(
        "app.main.YouTubeDataClient",
        lambda api_key: FakeYouTubeClient(),
    )

    response = client.get("/api/v1/trends?region=NG")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["video_id"] == "video123"
    assert data[0]["title"] == "Python for Beginners"
    assert data[0]["view_count"] == 12000
    assert data[0]["country_code"] == "NG"


def test_trends_reject_invalid_region():
    response = client.get("/api/v1/trends?region=NIG")

    assert response.status_code == 422


def test_trends_reject_invalid_limit():
    response = client.get("/api/v1/trends?limit=100")

    assert response.status_code == 422


def test_missing_api_key_returns_503(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_youtube_api_key",
        lambda: None,
    )

    response = client.get("/api/v1/trends")

    assert response.status_code == 503


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_youtube_client_sends_correct_parameters():
    def mock_handler(request):
        assert request.url.params["chart"] == "mostPopular"
        assert request.url.params["regionCode"] == "NG"
        assert request.url.params["maxResults"] == "5"

        return httpx.Response(
            200,
            json={"items": [{"id": "abc"}]},
        )

    transport = httpx.MockTransport(mock_handler)

    youtube = YouTubeDataClient(
        api_key="test-key",
        transport=transport,
    )

    result = youtube.get_most_popular_videos(
        region_code="NG",
        max_results=5,
    )

    assert result == [{"id": "abc"}]


def test_youtube_client_handles_api_failure():
    def mock_handler(request):
        return httpx.Response(403, json={"error": "Forbidden"})

    transport = httpx.MockTransport(mock_handler)

    youtube = YouTubeDataClient(
        api_key="test-key",
        transport=transport,
    )

    with pytest.raises(YouTubeAPIError):
        youtube.get_most_popular_videos("NG")
def test_missing_video_statistics_are_handled():
    class IncompleteYouTubeClient:
        def get_most_popular_videos(
            self,
            region_code,
            max_results=10,
            category_id=None,
        ):
            return [
                {
                    "id": "video456",
                    "snippet": {
                        "title": "Python Basics",
                        "channelTitle": "Learning Python",
                    },
                }
            ]

    trends = get_country_trends(
        client=IncompleteYouTubeClient(),
        region_code="NG",
    )

    assert len(trends) == 1
    assert trends[0].title == "Python Basics"
    assert trends[0].view_count is None
    assert trends[0].like_count is None
    assert trends[0].comment_count is None
    