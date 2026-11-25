
from pydantic import BaseModel


class VideoTrend(BaseModel):
    video_id: str
    title: str
    channel_title: str
    published_at: str | None = None
    country_code: str
    video_url: str
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None

    average_views_per_day: float | None = None
    engagement_rate: float | None = None

    # Research ranking
    research_priority_score: float | None = None
    score_breakdown: dict[str, float | None] | None = None

    # Historical trend metrics
    previous_view_count: int | None = None
    views_delta: int | None = None
    interval_days: float | None = None
    views_per_day_since_last_snapshot: float | None = None
    views_growth_percent: float | None = None
    trend_direction: str | None = None

    # Momentum
    previous_interval_views_per_day: float | None = None
    views_per_day_change: float | None = None
    momentum: str | None = None

