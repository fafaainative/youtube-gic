
from datetime import datetime, timezone
from math import isfinite


WEIGHTS = {
    "performance": 0.40,
    "engagement": 0.30,
    "freshness": 0.20,
    "popularity": 0.10,
}

FRESHNESS_HALF_LIFE_DAYS = 30


def min_max_normalize(values: list[float]) -> list[float]:
    """
    Convert numeric values into scores between 0 and 100.

    Equal values receive a neutral score of 50.
    """

    if not values:
        return []

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        return [50.0] * len(values)

    return [
        round((value - minimum) / (maximum - minimum) * 100, 2)
        for value in values
    ]


def calculate_freshness_score(
    published_at: str | None,
    as_of: datetime | None = None,
) -> float | None:
    """Calculate freshness using a 30-day half-life."""

    if not published_at:
        return None

    try:
        published_date = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )

        if published_date.tzinfo is None:
            published_date = published_date.replace(
                tzinfo=timezone.utc
            )

        current_date = as_of or datetime.now(timezone.utc)

        if current_date.tzinfo is None:
            current_date = current_date.replace(
                tzinfo=timezone.utc
            )

        age_days = (
            current_date - published_date
        ).total_seconds() / 86400

        if age_days < 0:
            return None

        score = 100 * (
            2 ** (-age_days / FRESHNESS_HALF_LIFE_DAYS)
        )

        return round(score, 2)

    except (ValueError, TypeError, OverflowError):
        return None


def calculate_research_priority_scores(
    videos: list,
    as_of: datetime | None = None,
) -> list:
    """
    Calculate sample-relative Research Priority Scores.

    The returned list is sorted from highest to lowest score.
    """

    if not videos:
        return []

    performance_values = [
        video.average_views_per_day
        for video in videos
    ]

    engagement_values = [
        video.engagement_rate
        for video in videos
    ]

    popularity_values = [
        video.view_count
        for video in videos
    ]

    performance_scores = min_max_normalize(
        [
            float(value)
            for value in performance_values
            if value is not None and isfinite(value)
        ]
    )

    engagement_scores = min_max_normalize(
        [
            float(value)
            for value in engagement_values
            if value is not None and isfinite(value)
        ]
    )

    popularity_scores = min_max_normalize(
        [
            float(value)
            for value in popularity_values
            if value is not None and isfinite(value)
        ]
    )

    def build_score_map(values):
        valid_values = [
            value
            for value in values
            if value is not None and isfinite(value)
        ]

        scores = min_max_normalize(
            [float(value) for value in valid_values]
        )

        iterator = iter(scores)

        return [
            next(iterator) if value is not None and isfinite(value)
            else None
            for value in values
        ]

    performance_scores = build_score_map(performance_values)
    engagement_scores = build_score_map(engagement_values)
    popularity_scores = build_score_map(popularity_values)

    scored_videos = []

    for index, video in enumerate(videos):

        freshness_score = calculate_freshness_score(
            video.published_at,
            as_of=as_of,
        )

        components = {
            "performance": performance_scores[index],
            "engagement": engagement_scores[index],
            "freshness": freshness_score,
            "popularity": popularity_scores[index],
        }

        available_components = {
            name: score
            for name, score in components.items()
            if score is not None
        }

        if not available_components:
            video.research_priority_score = None
            video.score_breakdown = components
            scored_videos.append(video)
            continue

        total_weight = sum(
            WEIGHTS[name]
            for name in available_components
        )

        weighted_score = sum(
            score * WEIGHTS[name]
            for name, score in available_components.items()
        )

        final_score = weighted_score / total_weight

        video.research_priority_score = round(
            final_score, 2
        )

        video.score_breakdown = components

        scored_videos.append(video)

    scored_videos.sort(
        key=lambda video: (
            video.research_priority_score is not None,
            video.research_priority_score or 0,
        ),
        reverse=True,
    )

    return scored_videos
