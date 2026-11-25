
from app.modules.trend_radar.trend_analysis import (
    analyze_video_trend,
    calculate_interval_metrics,
    calculate_acceleration,
)


def snapshot(views, timestamp):
    return {
        "video_id": "video123",
        "view_count": views,
        "observed_at": timestamp,
    }


def test_no_history_returns_new():
    result = analyze_video_trend([])

    assert result["trend_direction"] == "new"
    assert result["views_delta"] is None
    assert result["momentum"] == "insufficient_history"


def test_one_snapshot_has_insufficient_history():
    snapshots = [
        snapshot(10000, "2026-11-24T10:00:00+00:00"),
    ]

    result = analyze_video_trend(snapshots)

    assert result["trend_direction"] == "new"
    assert result["views_delta"] is None


def test_views_increased():
    previous = snapshot(
        10000,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        16000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_interval_metrics(
        current,
        previous,
    )

    assert result["views_delta"] == 6000
    assert result["interval_days"] == 1.0
    assert result["views_per_day_since_last_snapshot"] == 6000
    assert result["views_growth_percent"] == 60.0
    assert result["trend_direction"] == "growing"


def test_views_decreased():
    previous = snapshot(
        10000,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        9000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_interval_metrics(
        current,
        previous,
    )

    assert result["views_delta"] == -1000
    assert result["views_growth_percent"] == -10.0
    assert result["trend_direction"] == "declining"


def test_views_remained_stable():
    previous = snapshot(
        10000,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        10000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_interval_metrics(
        current,
        previous,
    )

    assert result["views_delta"] == 0
    assert result["views_growth_percent"] == 0.0
    assert result["trend_direction"] == "stable"


def test_zero_previous_views():
    previous = snapshot(
        0,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        100,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_interval_metrics(
        current,
        previous,
    )

    assert result["views_delta"] == 100
    assert result["views_growth_percent"] is None
    assert result["trend_direction"] == "growing"


def test_acceleration():
    older = snapshot(
        1000,
        "2026-11-22T10:00:00+00:00",
    )

    previous = snapshot(
        3000,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        8000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_acceleration(
        current,
        previous,
        older,
    )

    assert result["previous_interval_views_per_day"] == 2000
    assert result["views_per_day_change"] == 3000
    assert result["momentum"] == "accelerating"


def test_deceleration():
    older = snapshot(
        1000,
        "2026-11-22T10:00:00+00:00",
    )

    previous = snapshot(
        8000,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        10000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_acceleration(
        current,
        previous,
        older,
    )

    assert result["previous_interval_views_per_day"] == 7000
    assert result["views_per_day_change"] == -5000
    assert result["momentum"] == "decelerating"


def test_equal_rates_are_steady():
    older = snapshot(
        1000,
        "2026-11-22T10:00:00+00:00",
    )

    previous = snapshot(
        3000,
        "2026-11-23T10:00:00+00:00",
    )

    current = snapshot(
        5000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_acceleration(
        current,
        previous,
        older,
    )

    assert result["views_per_day_change"] == 0
    assert result["momentum"] == "steady"


def test_missing_previous_snapshot():
    current = snapshot(
        10000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_interval_metrics(
        current,
        None,
    )

    assert result["views_delta"] is None
    assert result["trend_direction"] == "new"


def test_zero_time_interval():
    previous = snapshot(
        10000,
        "2026-11-24T10:00:00+00:00",
    )

    current = snapshot(
        15000,
        "2026-11-24T10:00:00+00:00",
    )

    result = calculate_interval_metrics(
        current,
        previous,
    )

    assert result["views_delta"] == 5000
    assert result["interval_days"] is None
    assert result["views_per_day_since_last_snapshot"] is None
    assert result["trend_direction"] == "unknown"
