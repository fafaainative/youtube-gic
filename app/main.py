from fastapi import FastAPI, HTTPException, Query

from app.config import get_youtube_api_key
from app.integrations.youtube_client import (
    YouTubeAPIError,
    YouTubeDataClient,
)
from app.modules.trend_radar.schemas import VideoTrend
from app.modules.trend_radar.service import get_country_trends
from app.modules.trend_radar.tracking_service import (
    TrendTrackingService,
)

app = FastAPI(
    title="YouTube GIC API",
    description="Growth Intelligence for Creators",
    version="0.1.0",
)

trend_tracking_service = TrendTrackingService()


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
            tracking_service=trend_tracking_service,
        )

    except YouTubeAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/trends/{video_id}/history")
def video_trend_history(video_id: str):
    """
    Return historical trend analysis for a video.
    """
    snapshots = (
        trend_tracking_service.repository.get_recent_snapshots(
            video_id=video_id,
            limit=30,
        )
    )
    analysis = trend_tracking_service.analyse_video(
        video_id
    )
    return {
        "video_id": video_id,
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "trend_analysis": analysis,
    }
