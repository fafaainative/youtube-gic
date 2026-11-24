
from datetime import datetime, timezone


def calculate_average_views_per_day(
    view_count: int | None,
    published_at: str | None,
    as_of: datetime | None = None,
) -> float | None:
    """Calculate lifetime average views per day."""

    if view_count is None or view_count < 0 or not published_at:
        return None

    try:
        published_date = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )

        if published_date.tzinfo is None:
            published_date = published_date.replace(tzinfo=timezone.utc)

        current_date = as_of or datetime.now(timezone.utc)

        if current_date.tzinfo is None:
            current_date = current_date.replace(tzinfo=timezone.utc)

        elapsed_seconds = (
            current_date - published_date
        ).total_seconds()

        if elapsed_seconds <= 0:
            return None

        elapsed_days = elapsed_seconds / 86400

        return round(view_count / elapsed_days, 2)

    except (ValueError, TypeError, OverflowError):
        return None


def calculate_engagement_rate(
    view_count: int | None,
    like_count: int | None,
    comment_count: int | None,
) -> float | None:
    """Calculate public likes and comments as a percentage of views."""

    if (
        view_count is None
        or like_count is None
        or comment_count is None
        or view_count <= 0
        or like_count < 0
        or comment_count < 0
    ):
        return None

    return round(
        ((like_count + comment_count) / view_count) * 100,
        2,
    )
