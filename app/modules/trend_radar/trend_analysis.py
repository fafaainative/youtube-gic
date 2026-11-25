
from datetime import datetime, timezone


def parse_timestamp(value):
    """Convert a timestamp string to a timezone-aware datetime."""

    if not value:
        return None

    try:
        timestamp = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        return timestamp

    except (ValueError, TypeError):
        return None


def calculate_interval_metrics(
    current_snapshot,
    previous_snapshot,
):
    """
    Calculate view changes between two observations.
    """

    if not current_snapshot or not previous_snapshot:
        return {
            "views_delta": None,
            "interval_days": None,
            "views_per_day_since_last_snapshot": None,
            "views_growth_percent": None,
            "trend_direction": "new",
        }

    current_views = current_snapshot.get("view_count")
    previous_views = previous_snapshot.get("view_count")

    current_time = parse_timestamp(
        current_snapshot.get("observed_at")
    )

    previous_time = parse_timestamp(
        previous_snapshot.get("observed_at")
    )

    if (
        current_views is None
        or previous_views is None
        or current_time is None
        or previous_time is None
    ):
        return {
            "views_delta": None,
            "interval_days": None,
            "views_per_day_since_last_snapshot": None,
            "views_growth_percent": None,
            "trend_direction": "unknown",
        }

    views_delta = current_views - previous_views

    elapsed_seconds = (
        current_time - previous_time
    ).total_seconds()

    if elapsed_seconds <= 0:
        return {
            "views_delta": views_delta,
            "interval_days": None,
            "views_per_day_since_last_snapshot": None,
            "views_growth_percent": None,
            "trend_direction": "unknown",
        }

    interval_days = elapsed_seconds / 86400

    views_per_day = views_delta / interval_days

    if previous_views > 0:
        growth_percent = (
            views_delta / previous_views
        ) * 100
    else:
        growth_percent = None

    if views_delta > 0:
        direction = "growing"
    elif views_delta < 0:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "views_delta": views_delta,
        "interval_days": round(interval_days, 4),
        "views_per_day_since_last_snapshot": round(
            views_per_day, 2
        ),
        "views_growth_percent": (
            round(growth_percent, 2)
            if growth_percent is not None
            else None
        ),
        "trend_direction": direction,
    }


def calculate_acceleration(
    current_snapshot,
    previous_snapshot,
    older_snapshot,
):
    """
    Compare the latest daily-view rate with the preceding rate.

    Requires three snapshots.
    """

    if not older_snapshot:
        return {
            "previous_interval_views_per_day": None,
            "views_per_day_change": None,
            "momentum": "insufficient_history",
        }

    latest_metrics = calculate_interval_metrics(
        current_snapshot,
        previous_snapshot,
    )

    previous_interval_metrics = calculate_interval_metrics(
        previous_snapshot,
        older_snapshot,
    )

    latest_rate = latest_metrics[
        "views_per_day_since_last_snapshot"
    ]

    previous_rate = previous_interval_metrics[
        "views_per_day_since_last_snapshot"
    ]

    if latest_rate is None or previous_rate is None:
        return {
            "previous_interval_views_per_day": None,
            "views_per_day_change": None,
            "momentum": "unknown",
        }

    rate_change = latest_rate - previous_rate

    if rate_change > 0:
        momentum = "accelerating"
    elif rate_change < 0:
        momentum = "decelerating"
    else:
        momentum = "steady"

    return {
        "previous_interval_views_per_day": round(
            previous_rate, 2
        ),
        "views_per_day_change": round(
            rate_change, 2
        ),
        "momentum": momentum,
    }


def analyze_video_trend(snapshots):
    """
    Analyse a list of snapshots ordered newest first.

    snapshots[0] = current observation
    snapshots[1] = previous observation
    snapshots[2] = older observation
    """

    if not snapshots:
        return {
            "views_delta": None,
            "interval_days": None,
            "views_per_day_since_last_snapshot": None,
            "views_growth_percent": None,
            "trend_direction": "new",
            "previous_interval_views_per_day": None,
            "views_per_day_change": None,
            "momentum": "insufficient_history",
        }

    current = snapshots[0]

    previous = (
        snapshots[1]
        if len(snapshots) >= 2
        else None
    )

    older = (
        snapshots[2]
        if len(snapshots) >= 3
        else None
    )

    interval_metrics = calculate_interval_metrics(
        current,
        previous,
    )

    acceleration_metrics = calculate_acceleration(
        current,
        previous,
        older,
    )

    return {
        **interval_metrics,
        **acceleration_metrics,
    }
