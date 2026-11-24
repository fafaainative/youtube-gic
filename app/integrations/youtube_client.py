
import httpx


YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Raised when communication with YouTube fails."""


class YouTubeDataClient:
    """Handles communication with the YouTube Data API."""

    def __init__(self, api_key: str, transport=None):
        self.api_key = api_key
        self.transport = transport

    def get_most_popular_videos(
        self,
        region_code: str,
        max_results: int = 10,
        category_id: str | None = None,
    ) -> list[dict]:

        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
            "key": self.api_key,
        }

        if category_id:
            params["videoCategoryId"] = category_id

        try:
            with httpx.Client(
                base_url=YOUTUBE_API_BASE_URL,
                timeout=15.0,
                transport=self.transport,
            ) as client:

                response = client.get("/videos", params=params)
                response.raise_for_status()

                data = response.json()

                return data.get("items", [])

        except httpx.HTTPStatusError as exc:
            raise YouTubeAPIError(
                f"YouTube returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise YouTubeAPIError(
                "Unable to connect to YouTube."
            ) from exc
