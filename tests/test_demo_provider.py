from app.modules.trend_radar.metrics import calculate_engagement_rate
from app.ui.demo_provider import (
    COUNTRY_ALL,
    DEMO_CATALOG,
    DEMO_COUNTRIES,
    DemoTrendProvider,
)


def test_demo_trends_are_deterministic():
    provider = DemoTrendProvider()

    first = provider.get_country_trends("NG", limit=5)
    second = provider.get_country_trends("NG", limit=5)

    assert [
        (video.video_id, video.research_priority_score)
        for video in first
    ] == [
        (video.video_id, video.research_priority_score)
        for video in second
    ]


def test_demo_trends_do_not_require_api_key(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)

    videos = DemoTrendProvider().get_country_trends(
        "ZA", limit=5
    )

    assert len(videos) == 5


def test_country_category_and_format_filters():
    provider = DemoTrendProvider()

    all_videos = provider.get_country_trends(
        COUNTRY_ALL,
        limit=100,
    )

    assert len(all_videos) == len(DEMO_CATALOG)

    expected_countries = set(DEMO_COUNTRIES) - {COUNTRY_ALL}
    assert {
        video.country_code for video in all_videos
    } == expected_countries

    shorts = provider.get_country_trends(
        COUNTRY_ALL,
        video_format="Shorts",
        limit=100,
    )
    assert shorts
    assert all(
        provider.get_video_format(video.video_id) == "Shorts"
        for video in shorts
    )

    education = provider.get_country_trends(
        COUNTRY_ALL,
        category_id="27",
        limit=100,
    )
    assert education
    assert all(
        provider.get_video_category(video.video_id)
        == "Education"
        for video in education
    )


def test_empty_filter_result_is_empty():
    videos = DemoTrendProvider().get_country_trends(
        "NG",
        category_id="20",
        video_format="Shorts",
        limit=10,
    )

    assert videos == []


def test_videos_use_existing_metric_and_ranking_logic():
    provider = DemoTrendProvider()

    videos = provider.get_country_trends("NG", limit=5)

    scores = [
        video.research_priority_score for video in videos
    ]

    assert scores == sorted(scores, reverse=True)
    assert all(
        0 <= score <= 100 for score in scores
    )
    assert all(
        video.score_breakdown is not None
        for video in videos
    )

    record = next(
        item
        for item in DEMO_CATALOG
        if item.video_id == "demo_ng_001"
    )
    video = next(
        item
        for item in videos
        if item.video_id == "demo_ng_001"
    )

    assert video.engagement_rate == calculate_engagement_rate(
        view_count=record.view_count,
        like_count=record.like_count,
        comment_count=record.comment_count,
    )


def test_trend_fields_come_from_existing_analysis():
    provider = DemoTrendProvider()

    videos = provider.get_country_trends(
        COUNTRY_ALL,
        limit=100,
    )

    by_id = {
        video.video_id: video for video in videos
    }

    growing = by_id["demo_ng_001"]
    assert growing.trend_direction == "growing"
    assert growing.views_delta == 90000
    assert growing.momentum == "decelerating"

    stable = by_id["demo_ng_003"]
    assert stable.trend_direction == "stable"

    declining = by_id["demo_ng_004"]
    assert declining.trend_direction == "declining"

    new = by_id["demo_ng_005"]
    assert new.trend_direction == "new"
    assert new.momentum == "insufficient_history"


def test_history_returns_simulated_observations():
    provider = DemoTrendProvider()

    history = provider.get_video_history("demo_ng_001")

    assert len(history) == 3
    assert history[0]["view_count"] == 1280000
    assert history[1]["view_count"] == 1190000
    assert history[2]["view_count"] == 1080000
    assert provider.get_video_history("unknown") == []
