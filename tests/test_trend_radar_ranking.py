
from datetime import datetime, timezone

from app.modules.trend_radar.ranking import (
    calculate_freshness_score,
    calculate_research_priority_scores,
    min_max_normalize,
)
from app.modules.trend_radar.schemas import VideoTrend


AS_OF = datetime(2026, 11, 24, tzinfo=timezone.utc)


def make_video(
    video_id,
    views,
    average_views_per_day,
    engagement_rate,
    published_at,
):
    return VideoTrend(
        video_id=video_id,
        title=f"Video {video_id}",
        channel_title="Test Channel",
        published_at=published_at,
        country_code="NG",
        video_url=f"https://www.youtube.com/watch?v={video_id}",
        view_count=views,
        average_views_per_day=average_views_per_day,
        engagement_rate=engagement_rate,
    )


def test_min_max_normalize():
    result = min_max_normalize([10, 20, 30])

    assert result == [0.0, 50.0, 100.0]


def test_min_max_normalize_equal_values():
    result = min_max_normalize([10, 10, 10])

    assert result == [50.0, 50.0, 50.0]


def test_min_max_normalize_empty_values():
    result = min_max_normalize([])

    assert result == []


def test_freshness_score_for_new_video():
    result = calculate_freshness_score(
        "2026-11-24T00:00:00Z",
        as_of=AS_OF,
    )

    assert result == 100.0


def test_freshness_score_after_30_days():
    result = calculate_freshness_score(
        "2026-10-25T00:00:00Z",
        as_of=AS_OF,
    )

    assert result == 50.0


def test_freshness_score_for_invalid_date():
    result = calculate_freshness_score(
        "invalid-date",
        as_of=AS_OF,
    )

    assert result is None


def test_freshness_score_for_future_video():
    result = calculate_freshness_score(
        "2026-11-25T00:00:00Z",
        as_of=AS_OF,
    )

    assert result is None


def test_high_performance_video_ranks_higher():
    videos = [
        make_video(
            "low",
            views=1000,
            average_views_per_day=100,
            engagement_rate=2,
            published_at="2026-11-20T00:00:00Z",
        ),
        make_video(
            "high",
            views=100000,
            average_views_per_day=10000,
            engagement_rate=10,
            published_at="2026-11-23T00:00:00Z",
        ),
    ]

    result = calculate_research_priority_scores(
        videos,
        as_of=AS_OF,
    )

    assert result[0].video_id == "high"
    assert result[0].research_priority_score > (
        result[1].research_priority_score
    )


def test_score_is_between_zero_and_100():
    videos = [
        make_video(
            "a",
            views=1000,
            average_views_per_day=100,
            engagement_rate=2,
            published_at="2026-11-20T00:00:00Z",
        ),
        make_video(
            "b",
            views=2000,
            average_views_per_day=200,
            engagement_rate=4,
            published_at="2026-11-22T00:00:00Z",
        ),
    ]

    result = calculate_research_priority_scores(
        videos,
        as_of=AS_OF,
    )

    for video in result:
        assert 0 <= video.research_priority_score <= 100


def test_missing_metrics_do_not_crash_scoring():
    videos = [
        make_video(
            "a",
            views=None,
            average_views_per_day=None,
            engagement_rate=None,
            published_at="2026-11-20T00:00:00Z",
        ),
        make_video(
            "b",
            views=1000,
            average_views_per_day=100,
            engagement_rate=2,
            published_at="2026-11-22T00:00:00Z",
        ),
    ]

    result = calculate_research_priority_scores(
        videos,
        as_of=AS_OF,
    )

    assert len(result) == 2
    assert all(
        video.research_priority_score is not None
        for video in result
    )


def test_empty_video_list():
    result = calculate_research_priority_scores(
        [],
        as_of=AS_OF,
    )

    assert result == []
