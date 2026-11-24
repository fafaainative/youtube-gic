
from fastapi import FastAPI, HTTPException, Query

from app.config import get_youtube_api_key
from app.integrations.youtube_client import (
    YouTubeAPIError,
    YouTubeDataClient,
)
from app.modules.trend_radar.schemas import VideoTrend
from app.modules.trend_radar.service import get_country_trends


app = FastAPI(
    title="YouTube GIC API",
    description="Growth Intelligence for Creators",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "YouTube GIC",
    }


@app.get("/api/v1/trends", response_model=list[VideoTrend])
def country_trends(
    region: str = Query(
        default="NG",
        min_length=2,
        max_length=2,
        pattern="^[A-Za-z]{2}$",
    ),
    limit: int = Query(default=10, ge=1, le=50),
    category_id: str | None = None,
):
    api_key = get_youtube_api_key()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="YouTube API key is not configured.",
        )

    client = YouTubeDataClient(api_key=api_key)

    try:
        return get_country_trends(
            client=client,
            region_code=region.upper(),
            limit=limit,
            category_id=category_id,
        )

    except YouTubeAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
