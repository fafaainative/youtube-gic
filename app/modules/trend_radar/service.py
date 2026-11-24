
from datetime import datetime

from app.integrations.youtube_client import YouTubeDataClient
from app.modules.trend_radar.metrics import (
    calculate_average_views_per_day,
    calculate_engagement_rate,
)
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
    as_of: datetime | None = None,
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

        if not video_id:
            continue

        snippet = item.get("snippet") or {}
        statistics = item.get("statistics") or {}

        view_count = safe_integer(statistics.get("viewCount"))
        like_count = safe_integer(statistics.get("likeCount"))
        comment_count = safe_integer(statistics.get("commentCount"))

        published_at = snippet.get("publishedAt")

        average_views_per_day = calculate_average_views_per_day(
            view_count=view_count,
            published_at=published_at,
            as_of=as_of,
        )

        engagement_rate = calculate_engagement_rate(
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
        )

        trend = VideoTrend(
            video_id=video_id,
            title=snippet.get("title", "Untitled"),
            channel_title=snippet.get("channelTitle", "Unknown channel"),
            published_at=published_at,
            country_code=region_code,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            average_views_per_day=average_views_per_day,
            engagement_rate=engagement_rate,
        )

        trends.append(trend)

    return trends
