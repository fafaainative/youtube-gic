from app.ui.demo_provider import DemoTrendProvider
from app.ui.formatting import (
    build_video_table,
    format_count,
    format_date,
    format_percent,
    format_score,
)


def test_format_count():
    assert format_count(None) == "—"
    assert format_count(987) == "987"
    assert format_count(1500) == "1.5K"
    assert format_count(1280000) == "1.28M"


def test_format_percent_and_score():
    assert format_percent(None) == "—"
    assert format_percent(7.256) == "7.26%"
    assert format_score(None) == "—"
    assert format_score(82.5) == "82.50"


def test_format_date_handles_utc_and_missing_values():
    assert format_date("2026-11-20T10:00:00Z") == "20 Nov 2026"
    assert format_date(None) == "—"


def test_build_video_table_contains_required_columns():
    provider = DemoTrendProvider()

    videos = provider.get_country_trends("NG", limit=3)
    rows = build_video_table(videos, provider)

    required_columns = {
        "Video title",
        "Channel",
        "Views",
        "Likes",
        "Comments",
        "Engagement rate",
        "Average views/day",
        "Research Priority Score",
        "Trend direction",
    }

    assert len(rows) == 3
    assert required_columns.issubset(rows[0])
    assert rows[0]["Category"] != "—"
    assert rows[0]["Format"] != "—"
    assert rows[0]["Engagement rate"].endswith("%")
