
from datetime import datetime, timezone

from app.modules.trend_radar.metrics import (
    calculate_average_views_per_day,
    calculate_engagement_rate,
)


def test_average_views_per_day():
    as_of = datetime(2026, 11, 24, tzinfo=timezone.utc)

    result = calculate_average_views_per_day(
        view_count=20000,
        published_at="2026-11-22T00:00:00Z",
        as_of=as_of,
    )

    assert result == 10000.0


def test_average_views_returns_none_without_view_count():
    result = calculate_average_views_per_day(
        view_count=None,
        published_at="2026-11-22T00:00:00Z",
    )

    assert result is None


def test_average_views_returns_none_for_invalid_date():
    result = calculate_average_views_per_day(
        view_count=20000,
        published_at="not-a-valid-date",
    )

    assert result is None


def test_average_views_returns_none_for_future_publication():
    as_of = datetime(2026, 11, 24, tzinfo=timezone.utc)

    result = calculate_average_views_per_day(
        view_count=20000,
        published_at="2026-11-25T00:00:00Z",
        as_of=as_of,
    )

    assert result is None


def test_engagement_rate():
    result = calculate_engagement_rate(
        view_count=10000,
        like_count=800,
        comment_count=200,
    )

    assert result == 10.0


def test_engagement_rate_returns_none_when_data_is_missing():
    result = calculate_engagement_rate(
        view_count=10000,
        like_count=None,
        comment_count=200,
    )

    assert result is None


def test_engagement_rate_returns_none_when_views_are_zero():
    result = calculate_engagement_rate(
        view_count=0,
        like_count=100,
        comment_count=20,
    )

    assert result is None
