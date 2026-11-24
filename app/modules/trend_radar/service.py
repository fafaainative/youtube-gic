
from app.integrations.youtube_client import YouTubeDataClient
from app.modules.trend_radar.schemas import VideoTrend


def safe_integer(value):
    """Convert a value to an integer without crashing."""
    if value is None:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def get_country_trends(
    client: YouTubeDataClient,
    region_code: str,
    limit: int = 10,
    category_id: str | None = None,
) -> list[VideoTrend]:
    """
    Retrieve popular videos and convert them into
    YouTube GIC's internal VideoTrend format.
    """

    items = client.get_most_popular_videos(
        region_code=region_code,
        max_results=limit,
        category_id=category_id,
    )

    trends = []

    for item in items:
        video_id = item.get("id")
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        if not video_id:
            continue

        trend = VideoTrend(
            video_id=video_id,
            title=snippet.get("title", "Untitled"),
            channel_title=snippet.get(
                "channelTitle", "Unknown channel"
            ),
            published_at=snippet.get("publishedAt"),
            country_code=region_code,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            view_count=safe_integer(
                statistics.get("viewCount")
            ),
            like_count=safe_integer(
                statistics.get("likeCount")
            ),
            comment_count=safe_integer(
                statistics.get("commentCount")
            ),
        )

        trends.append(trend)

    return trends
