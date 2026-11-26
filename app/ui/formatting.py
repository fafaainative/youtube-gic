from app.modules.trend_radar.trend_analysis import parse_timestamp


def format_count(value):
    """Format a numeric value for compact display."""

    if value is None:
        return "—"

    number = float(value)

    if number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"

    if number >= 1_000:
        return f"{number / 1_000:.1f}K"

    return f"{int(number):,}"


def format_percent(value):
    """Format a percentage value for display."""

    if value is None:
        return "—"

    return f"{float(value):.2f}%"


def format_score(value):
    """Format a Research Priority Score for display."""

    if value is None:
        return "—"

    return f"{float(value):.2f}"


def format_date(value):
    """Format an ISO timestamp as a short readable date."""

    timestamp = parse_timestamp(value)

    if timestamp is None:
        return "—"

    return timestamp.strftime("%d %b %Y")


def build_video_table(videos, provider=None):
    """Build display rows from VideoTrend objects."""

    rows = []

    for video in videos:
        category = (
            provider.get_video_category(video.video_id)
            if provider is not None
            else None
        )
        video_format = (
            provider.get_video_format(video.video_id)
            if provider is not None
            else None
        )

        rows.append(
            {
                "Video title": video.title,
                "Channel": video.channel_title,
                "Views": format_count(video.view_count),
                "Likes": format_count(video.like_count),
                "Comments": format_count(video.comment_count),
                "Engagement rate": format_percent(
                    video.engagement_rate
                ),
                "Average views/day": format_count(
                    video.average_views_per_day
                ),
                "Research Priority Score": format_score(
                    video.research_priority_score
                ),
                "Trend direction": (
                    video.trend_direction or "—"
                ),
                "Category": category or "—",
                "Format": video_format or "—",
            }
        )

    return rows
