import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.trend_radar.tracking_service import TrendTrackingService
from app.storage.snapshots import SnapshotRepository
from app.modules.trend_radar.schemas import VideoTrend


BASE_TIME = datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc)


def make_video(view_count=1000):
    return VideoTrend(
        video_id="video_123",
        title="Test Video",
        channel_title="Test Channel",
        published_at="2026-11-20T10:00:00Z",
        country_code="NG",
        video_url="https://www.youtube.com/watch?v=video_123",
        view_count=view_count,
        like_count=100,
        comment_count=10,
    )


def make_service(database_path, interval=timedelta(minutes=60)):
    repository = SnapshotRepository(database_path=database_path)

    service = TrendTrackingService(
        repository=repository,
        min_collection_interval=interval,
    )

    return service, repository


def at(minutes=0):
    return BASE_TIME + timedelta(minutes=minutes)


def seed_raw_snapshot(database_path, video, observed_at, view_count):
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO video_snapshots (
                video_id,
                observed_at,
                region_code,
                title,
                channel_title,
                published_at,
                view_count,
                like_count,
                comment_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                video.video_id,
                observed_at,
                video.country_code,
                video.title,
                video.channel_title,
                video.published_at,
                view_count,
                video.like_count,
                video.comment_count,
            ),
        )


def test_record_and_analyse(tmp_path):
    database_path = tmp_path / "test_tracking.db"

    repository = SnapshotRepository(database_path=database_path)

    tracking_service = TrendTrackingService(repository=repository)

    video = make_video()

    result = tracking_service.record_and_analyse(
        video=video,
        observed_at=datetime(2026, 11, 25, 10, 0, 0, tzinfo=timezone.utc),
    )

    assert result["trend_direction"] == "new"

    assert repository.get_snapshot_count("video_123") == 1


def test_first_observation_is_recorded(tmp_path):
    service, repository = make_service(
        tmp_path / "first_observation.db"
    )

    result = service.record_and_analyse(
        make_video(),
        observed_at=at(),
    )

    assert repository.get_snapshot_count("video_123") == 1
    assert result["trend_direction"] == "new"


def test_cooldown_prevents_new_observation(tmp_path):
    service, repository = make_service(
        tmp_path / "cooldown.db"
    )

    repository.save_snapshot(
        make_video(1000),
        observed_at=at(),
    )

    service.record_and_analyse(
        make_video(1200),
        observed_at=at(30),
    )

    assert repository.get_snapshot_count("video_123") == 1


def test_cooldown_expiration_permits_new_observation(tmp_path):
    service, repository = make_service(
        tmp_path / "cooldown_expiry.db"
    )

    repository.save_snapshot(
        make_video(1000),
        observed_at=at(),
    )

    result = service.record_and_analyse(
        make_video(1200),
        observed_at=at(60),
    )

    assert repository.get_snapshot_count("video_123") == 2
    assert result["views_delta"] == 200
    assert result["trend_direction"] == "growing"


def test_beyond_cooldown_permits_new_observation(tmp_path):
    service, repository = make_service(
        tmp_path / "beyond_cooldown.db"
    )

    repository.save_snapshot(
        make_video(1000),
        observed_at=at(),
    )

    result = service.record_and_analyse(
        make_video(1200),
        observed_at=at(120),
    )

    assert repository.get_snapshot_count("video_123") == 2
    assert result["views_delta"] == 200


def test_analysis_still_runs_when_snapshot_is_skipped(tmp_path):
    service, repository = make_service(
        tmp_path / "skipped_analysis.db"
    )

    repository.save_snapshot(
        make_video(900),
        observed_at=at(-60),
    )
    repository.save_snapshot(
        make_video(1000),
        observed_at=at(),
    )

    result = service.record_and_analyse(
        make_video(1200),
        observed_at=at(30),
    )

    assert repository.get_snapshot_count("video_123") == 2
    assert result["views_delta"] == 100
    assert result["interval_days"] == 0.0417
    assert result["trend_direction"] == "growing"


def test_interval_is_configurable(tmp_path):
    service, repository = make_service(
        tmp_path / "configurable.db",
        interval=timedelta(minutes=15),
    )

    repository.save_snapshot(
        make_video(1000),
        observed_at=at(),
    )

    service.record_and_analyse(
        make_video(1100),
        observed_at=at(10),
    )

    assert repository.get_snapshot_count("video_123") == 1

    result = service.record_and_analyse(
        make_video(1200),
        observed_at=at(15),
    )

    assert repository.get_snapshot_count("video_123") == 2
    assert result["views_delta"] == 200


def test_out_of_order_observation_is_skipped(tmp_path):
    service, repository = make_service(
        tmp_path / "out_of_order.db"
    )

    repository.save_snapshot(
        make_video(1000),
        observed_at=at(),
    )

    result = service.record_and_analyse(
        make_video(1100),
        observed_at=at(-60),
    )

    assert repository.get_snapshot_count("video_123") == 1
    assert result["trend_direction"] == "new"
    assert result["views_delta"] is None


@pytest.mark.parametrize(
    ("latest_timestamp", "observation_timestamp"),
    [
        (
            "2026-11-25T10:00:00Z",
            "2026-11-25T11:00:00+00:00",
        ),
        (
            "2026-11-25T10:00:00+00:00",
            "2026-11-25T11:00:00Z",
        ),
    ],
)
def test_utc_timestamp_formats_are_compatible(
    tmp_path,
    latest_timestamp,
    observation_timestamp,
):
    database_path = tmp_path / "timezone_formats.db"

    repository = SnapshotRepository(database_path=database_path)
    service = TrendTrackingService(repository=repository)

    seed_raw_snapshot(
        database_path,
        make_video(),
        latest_timestamp,
        1000,
    )

    result = service.record_and_analyse(
        make_video(1200),
        observed_at=observation_timestamp,
    )

    assert repository.get_snapshot_count("video_123") == 2
    assert result["trend_direction"] == "growing"


def test_naive_timestamps_are_treated_as_utc(tmp_path):
    service, repository = make_service(
        tmp_path / "naive_timestamps.db"
    )

    repository.save_snapshot(
        make_video(1000),
        observed_at=datetime(2026, 11, 25, 10, 0),
    )

    service.record_and_analyse(
        make_video(1100),
        observed_at=datetime(2026, 11, 25, 10, 30),
    )

    assert repository.get_snapshot_count("video_123") == 1

    result = service.record_and_analyse(
        make_video(1200),
        observed_at=datetime(2026, 11, 25, 11, 0),
    )

    assert repository.get_snapshot_count("video_123") == 2
    assert result["trend_direction"] == "growing"


def test_previous_snapshots_are_preserved(tmp_path):
    service, repository = make_service(
        tmp_path / "preserved.db"
    )

    first_time = at()
    second_time = at(60)
    third_time = at(120)

    service.record_and_analyse(
        make_video(1000),
        observed_at=first_time,
    )
    service.record_and_analyse(
        make_video(1100),
        observed_at=second_time,
    )
    service.record_and_analyse(
        make_video(1200),
        observed_at=third_time,
    )

    assert repository.get_snapshot_count("video_123") == 3

    snapshots = repository.get_recent_snapshots(
        "video_123",
        limit=10,
    )

    observed_counts = {
        snapshot["observed_at"]: snapshot["view_count"]
        for snapshot in snapshots
    }

    assert observed_counts == {
        first_time.isoformat(): 1000,
        second_time.isoformat(): 1100,
        third_time.isoformat(): 1200,
    }
