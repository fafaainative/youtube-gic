# YouTube GIC — Administrator and Developer Guide

This guide is for developers and system administrators working on the YouTube GIC backend. It describes the implementation that exists in this repository today.

## 1. Project architecture

YouTube GIC is a FastAPI application using Pydantic models, SQLite persistence and the YouTube Data API v3 through HTTPX.

The current request flow for country trends is:

1. `app/main.py` validates query parameters and reads the API key.
2. `app/integrations/youtube_client.py` calls YouTube's `/videos` endpoint with `chart=mostPopular`.
3. `app/modules/trend_radar/service.py` converts returned items into `VideoTrend` objects.
4. `app/modules/trend_radar/metrics.py` calculates derived performance metrics.
5. `app/modules/trend_radar/ranking.py` calculates the relative Research Priority Score and sorts videos.
6. `app/modules/trend_radar/tracking_service.py` applies the collection cooldown, saves allowed snapshots and runs historical analysis.
7. `app/modules/trend_radar/trend_analysis.py` compares stored snapshots.
8. `app/storage/snapshots.py` persists and retrieves observations in SQLite.
9. `app/main.py` returns the enriched video list or a mapped HTTP error.

There is no frontend, scheduler, message queue or authentication layer.

## 2. Directory structure

```text
youtube-gic/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── integrations/
│   │   └── youtube_client.py
│   ├── modules/
│   │   └── trend_radar/
│   │       ├── metrics.py
│   │       ├── ranking.py
│   │       ├── schemas.py
│   │       ├── service.py
│   │       ├── tracking_service.py
│   │       └── trend_analysis.py
│   └── storage/
│       ├── __init__.py
│       └── snapshots.py
├── docs/
│   ├── admin.md
│   ├── design-decisions.md
│   └── users.md
├── tests/
│   ├── test_snapshots.py
│   ├── test_tracking_service.py
│   ├── test_trend_api_cooldown.py
│   ├── test_trend_api_tracking.py
│   ├── test_trend_radar.py
│   ├── test_trend_radar_metrics.py
│   ├── test_trend_radar_ranking.py
│   └── test_trend_tracking.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

An ignored `.venv/` directory may exist after local setup. An ignored `data/` directory may be created at runtime for SQLite files.

## 3. Backend components and responsibilities

### `app/main.py`

- Creates the FastAPI application.
- Creates one module-level `TrendTrackingService()` instance.
- Defines `/health`, `/api/v1/trends` and `/api/v1/trends/{video_id}/history`.
- Maps a missing API key to HTTP `503`.
- Maps `YouTubeAPIError` to HTTP `502`.
- Reads up to 30 recent snapshots for the history endpoint.

### `app/config.py`

- `get_youtube_api_key()` reads `YOUTUBE_API_KEY` with `os.getenv`.
- Returns `None` when the variable is absent, empty or whitespace-only.
- No other environment variable is read by the application.

### `app/integrations/youtube_client.py`

- `YouTubeDataClient` builds a request to `https://www.googleapis.com/youtube/v3/videos`.
- Request parameters include `part=snippet,statistics`, `chart=mostPopular`, `regionCode`, `maxResults` and the API key.
- `videoCategoryId` is added only when `category_id` is supplied.
- `YouTubeAPIError` is raised for HTTP status errors and connection errors.

### `app/modules/trend_radar/service.py`

- `get_country_trends()` fetches items and builds `VideoTrend` objects.
- `safe_integer()` converts YouTube statistic strings to integers without raising.
- Missing video IDs are skipped.
- Ranked videos are enriched with historical analysis fields when a tracking service is supplied.

### `app/modules/trend_radar/schemas.py`

`VideoTrend` includes public identity fields, public statistics, calculated metrics, ranking fields and historical trend fields. Missing numeric values are optional and may be `None`.

### `app/modules/trend_radar/metrics.py`

- Average views per day = views divided by days since publication.
- Engagement rate = `(likes + comments) / views * 100`.
- Invalid or missing inputs return `None`.

### `app/modules/trend_radar/ranking.py`

- Weights: performance 40%, engagement 30%, freshness 20%, popularity 10%.
- Performance, engagement and popularity are normalised within the current sample.
- Freshness uses a 30-day exponential half-life.
- Missing components are excluded and remaining weights are adjusted.
- Results are sorted by score descending.

### `app/modules/trend_radar/trend_analysis.py`

- `parse_timestamp()` converts `Z`, `+00:00` and naive timestamps to timezone-aware UTC values.
- `calculate_interval_metrics()` computes view change, interval days, interval rate and growth percentage.
- `calculate_acceleration()` compares the latest interval rate with the preceding one.
- `analyze_video_trend()` combines interval metrics and momentum for snapshots ordered newest first.

### `app/modules/trend_radar/tracking_service.py`

- `should_record_snapshot()` is the pure collection decision function.
- `TrendTrackingService` fetches the latest snapshot, applies the decision, saves an allowed observation and always runs analysis.
- The collection interval is configurable per service instance.

### `app/storage/snapshots.py`

- `SnapshotRepository` owns SQLite persistence only.
- It does not apply cooldown policy.
- It normalises observation timestamps to UTC before storing them.

## 4. Installation

Python 3.12.3 was used for verification in this environment. The `python` command was not available; `python3` was used.

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`requirements.txt` currently declares:

```text
fastapi
uvicorn[standard]
httpx
httpx2
pytest
```

Application code imports `httpx`. Both `httpx` and `httpx2` are declared in the requirements file and installed successfully in the verification environment.

`.venv/` is excluded by `.gitignore`.

## 5. Environment variables

Only one environment variable is used by the application:

| Variable | Purpose | Required for |
| --- | --- | --- |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | `/api/v1/trends` |

Set it in the shell that starts the server:

```bash
export YOUTUBE_API_KEY="your_real_key"
```

`.env.example` lists this variable. The application does not automatically parse a `.env` file.

Do not commit real keys.

## 6. Running the application

From the repository root:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

The default address is `http://127.0.0.1:8000`.

A brief server start was verified with:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Calling `/health` on that instance returned:

```json
{"status": "healthy", "application": "YouTube GIC"}
```

## 7. Running tests

From the repository root:

```bash
.venv/bin/python -m pytest tests/test_tracking_service.py -v
.venv/bin/python -m pytest tests/test_trend_api_tracking.py -v
.venv/bin/python -m pytest -v
```

Recorded results during this work using `.venv/bin/python`:

- Before implementation: `45 passed` for `.venv/bin/python -m pytest -v`.
- After implementation: `12 passed` for `tests/test_tracking_service.py`.
- After implementation: `2 passed` for `tests/test_trend_api_tracking.py`.
- After implementation: `57 passed` for the complete suite.
- No test failures and no pytest warnings were reported in those runs.

No test uses `time.sleep()`. Cooldown tests use explicit observation timestamps and temporary SQLite databases.

## 8. SQLite database location

The default path is defined in `app/storage/snapshots.py`:

```python
DEFAULT_DATABASE_PATH = Path("data/trend_snapshots.db")
```

The path is relative to the process's current working directory. The repository creates the parent directory automatically when a file-based database is used.

If uvicorn is started from the repository root, the database will be `data/trend_snapshots.db`.

`.gitignore` excludes `data/*.db`, `data/*.sqlite` and `data/*.sqlite3`.

## 9. Snapshot schema overview

Table: `video_snapshots`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Internal row identifier |
| `video_id` | `TEXT NOT NULL` | YouTube video ID |
| `observed_at` | `TEXT NOT NULL` | UTC ISO timestamp string |
| `region_code` | `TEXT NOT NULL` | Country code from the request |
| `title` | `TEXT NOT NULL` | Video title |
| `channel_title` | `TEXT NOT NULL` | Channel title |
| `published_at` | `TEXT` | YouTube publication timestamp, nullable |
| `view_count` | `INTEGER` | Nullable |
| `like_count` | `INTEGER` | Nullable |
| `comment_count` | `INTEGER` | Nullable |

Index: `idx_video_snapshots_video_time` on `(video_id, observed_at)`.

There is no migration framework and no schema version table.

## 10. Historical tracking behaviour

- Collection starts when a successful `/api/v1/trends` request retrieves videos and a tracking service is attached.
- `get_country_trends()` calls `tracking_service.record_and_analyse(video)` for each ranked video.
- `record_and_analyse()` attempts recording and then always calls `analyse_video()`.
- Analysis reads the three most recent snapshots for that video.
- Analysis results are attached to the `VideoTrend` response using `setattr`.
- The history endpoint reads up to 30 recent snapshots for display and computes analysis from the three most recent.
- `snapshot_count` in the history response is the number of snapshots returned in that response, up to 30. It is not a total table count.
- Previous snapshots are not updated or deleted by the collection flow.

## 11. Cooldown configuration

Default interval: 60 minutes.

The default is the module constant:

```python
DEFAULT_MIN_COLLECTION_INTERVAL = timedelta(minutes=60)
```

`TrendTrackingService` accepts an optional `min_collection_interval` as a `timedelta`:

```python
from datetime import timedelta

from app.modules.trend_radar.tracking_service import TrendTrackingService

tracking_service = TrendTrackingService(
    min_collection_interval=timedelta(minutes=15),
)
```

There is no environment variable, settings file, API parameter or CLI flag for this interval. The global service in `app/main.py` uses the 60-minute default.

Decision policy:

- No latest snapshot: record immediately.
- Observation timestamp earlier than or equal to the latest snapshot: skip.
- Elapsed time less than the configured interval: skip.
- Elapsed time at or above the configured interval: record.
- Unparseable timestamp: skip recording rather than risk misleading history.
- Analysis always runs after the decision.

Timestamp handling:

- Timezone-aware values are converted to UTC.
- Naive values are treated as UTC.
- Strings containing `Z` or `+00:00` are parsed through `trend_analysis.parse_timestamp()`.

## 12. API endpoint overview

### `GET /health`

Returns application status. No API key required.

### `GET /api/v1/trends`

Query parameters:

| Parameter | Type | Default | Validation |
| --- | --- | --- | --- |
| `region` | string | `NG` | Exactly two letters |
| `limit` | integer | `10` | `1` to `50` |
| `category_id` | string or absent | absent | Passed through to YouTube |

Responses:

- `200`: list of enriched `VideoTrend` objects.
- `422`: invalid query parameters.
- `503`: `YOUTUBE_API_KEY` is not configured.
- `502`: YouTube returned an HTTP error or connection failed.

### `GET /api/v1/trends/{video_id}/history`

Returns:

```json
{
  "video_id": "string",
  "snapshot_count": 0,
  "snapshots": [],
  "trend_analysis": {}
}
```

No API key is needed for the history endpoint. It reads the same SQLite database as the trends endpoint.

## 13. Troubleshooting

**`python` command not found.**  
Use `python3` in this environment.

**`pytest` is not available to system Python.**  
Create the ignored virtual environment and install requirements, then use `.venv/bin/python -m pytest -v`.

**Trends endpoint returns `503`.**  
`YOUTUBE_API_KEY` is missing or empty in the server process environment. Restart the server after setting it.

**Trends endpoint returns `422`.**  
Check `region` length and format and the `limit` range.

**Trends endpoint returns `502`.**  
The YouTube client raised `YouTubeAPIError`. Check key validity, API enablement, quota and network connectivity.

**No snapshots are being created.**  
Check the cooldown window, the video ID, and whether requests are reaching `/api/v1/trends`. Only successful trends requests collect snapshots.

**History appears empty.**  
The video ID may differ, or no successful collection has happened. Verify the ID exactly as returned by the trends endpoint.

**Database file appears in an unexpected place.**  
The path is relative to the current working directory. Check where uvicorn was started.

**Permission error creating `data/`.**  
The process must be able to create and write the directory and database file.

**Import errors after changing code.**  
Confirm commands are run from the repository root with the virtual environment interpreter.

## 14. Logging and error handling

- No application-specific logging framework or log file is configured.
- Uvicorn provides its default server access logging when started through the CLI.
- Missing API key is handled with a FastAPI `HTTPException(503)`.
- Query validation errors are handled by FastAPI as HTTP `422`.
- `YouTubeAPIError` is caught in `/api/v1/trends` and converted to HTTP `502`.
- Metric and timestamp parsing helpers return `None` for invalid values instead of raising.
- The cooldown decision skips recording when timestamps cannot be compared; analysis still runs with stored data.
- SQLite writes use connection context managers.
- There is no retry mechanism, circuit breaker or structured audit log.

## 15. Security considerations

- The YouTube API key is read from the environment and must not be committed.
- The YouTube integration sends the key as a query parameter to Google. Avoid logging outbound request URLs that contain the key.
- The API currently has no authentication or authorisation. Do not expose it directly to untrusted networks without adding protection.
- SQL statements use parameter placeholders; user-provided video IDs are not string-concatenated into SQL.
- CORS is not configured.
- There is no rate limiting on API endpoints; the cooldown limits snapshot creation, not HTTP requests.
- The local SQLite database contains public video data but should still be protected by filesystem permissions.
- `requirements.txt` does not pin versions or include hashes. Use dependency locking before production deployment.

## 16. Git development workflow

Current branch at the time of this work: `feat/1-trend-radar-api`.

Read-only inspection commands:

```bash
git status
git branch --show-current
git diff
git diff --check
git log --oneline -10
```

Typical development workflow, not executed as part of this task:

```bash
git add <specific-files>
git commit -m "describe the change"
git push
```

Changes from this task were left unstaged and uncommitted for human review.

## 17. Current technical limitations

- No frontend and no user accounts.
- No scheduler or background worker.
- Snapshots happen only when the trends endpoint is requested.
- SQLite is local and single-file; no migration tooling is present.
- History responses return up to 30 snapshots and no pagination.
- The cooldown interval is code-configured per service instance, not environment-configured.
- Research Priority Score is experimental and sample-relative.
- Average views per day is a lifetime average, not current velocity.
- YouTube API quota and hidden engagement fields can limit data quality.
- No structured logging, metrics endpoint or health dependency checks.
- Dependencies are unpinned.
- No CI configuration is present in the repository.

## 18. Future development opportunities

These are not implemented:

- Scheduled or background snapshot collection.
- Environment-based configuration for the collection interval.
- Authentication, rate limiting and CORS policy.
- Database migrations and operational tooling for SQLite or a managed database.
- Historical pagination and retention policy.
- Structured logging and error metrics.
- API-level test coverage for every error branch.
- Dependency pinning and automated CI.
- User-facing search, niche analysis and saved research lists.
- Validation of the initial Research Priority Score weights against real creator research outcomes.
