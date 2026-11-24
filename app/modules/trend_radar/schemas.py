
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
