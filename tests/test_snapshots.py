
from datetime import datetime, timezone

from app.storage.snapshots import SnapshotRepository
from app.modules.trend_radar.schemas import VideoTrend


def make_video():
    return VideoTrend(
        video_id="video123",
        title="Python Tutorial",
        channel_title="Code Channel",
        published_at="2026-11-20T10:00:00Z",
        country_code="NG",
        video_url="https://www.youtube.com/watch?v=video123",
        view_count=10000,
        like_count=500,
        comment_count=100,
    )


def test_repository_creates_database(tmp_path):
    database_path = tmp_path / "snapshots.db"

    repository = SnapshotRepository(database_path)

    assert database_path.exists()


def test_save_snapshot(tmp_path):
    repository = SnapshotRepository(
        tmp_path / "snapshots.db"
    )

    video = make_video()

    observed_at = datetime(
        2026, 11, 24, 10, 0,
        tzinfo=timezone.utc,
    )

    repository.save_snapshot(
        video,
        observed_at=observed_at,
    )

    assert repository.get_snapshot_count("video123") == 1


def test_previous_snapshot_is_retrieved(tmp_path):
    repository = SnapshotRepository(
        tmp_path / "snapshots.db"
    )

    video = make_video()

    previous_time = datetime(
        2026, 11, 23, 10, 0,
        tzinfo=timezone.utc,
    )

    repository.save_snapshot(
        video,
        observed_at=previous_time,
    )

    current_time = datetime(
        2026, 11, 24, 10, 0,
        tzinfo=timezone.utc,
    )

    previous = repository.get_previous_snapshot(
        video_id="video123",
        before_timestamp=current_time,
    )

    assert previous is not None
    assert previous["view_count"] == 10000
    assert previous["video_id"] == "video123"


def test_previous_snapshot_returns_none_when_missing(tmp_path):
    repository = SnapshotRepository(
        tmp_path / "snapshots.db"
    )

    current_time = datetime(
        2026, 11, 24, 10, 0,
        tzinfo=timezone.utc,
    )

    previous = repository.get_previous_snapshot(
        video_id="unknown",
        before_timestamp=current_time,
    )

    assert previous is None


def test_multiple_snapshots_are_preserved(tmp_path):
    repository = SnapshotRepository(
        tmp_path / "snapshots.db"
    )

    video = make_video()

    first = datetime(
        2026, 11, 22, 10, 0,
        tzinfo=timezone.utc,
    )

    second = datetime(
        2026, 11, 23, 10, 0,
        tzinfo=timezone.utc,
    )

    third = datetime(
        2026, 11, 24, 10, 0,
        tzinfo=timezone.utc,
    )

    repository.save_snapshot(video, observed_at=first)
    repository.save_snapshot(video, observed_at=second)
    repository.save_snapshot(video, observed_at=third)

    assert repository.get_snapshot_count("video123") == 3

    previous = repository.get_previous_snapshot(
        "video123",
        third,
    )

    assert previous["observed_at"] == second.isoformat()
