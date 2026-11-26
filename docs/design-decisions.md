# YouTube GIC — Engineering Design Decisions

## DD-001: Separation of Responsibilities

**Status:** Accepted

### Context

YouTube GIC needs to retrieve external YouTube data, process that data into application-specific structures, and expose functionality through an API.

Combining these responsibilities in one module would increase coupling and make testing, maintenance and future development more difficult.

### Decision

The application will separate responsibilities into three layers:

1. **Integration layer:** `app/integrations/youtube_client.py` handles communication with external services.
2. **Business logic layer:** `app/modules/trend_radar/service.py` processes retrieved data and implements TrendRadar operations.
3. **API layer:** `app/main.py` exposes application functionality through FastAPI endpoints.

### Consequences

- Each layer has a clearly defined responsibility.
- External integrations can be mocked during testing.
- Business logic can be tested independently of HTTP requests.
- API endpoints remain relatively small.
- Future modules can reuse shared integrations where appropriate.

### Trade-offs

This introduces more files and some additional architectural structure. However, the separation is justified because YouTube GIC is intended to grow into a multi-module application.

### Verification

The architecture is supported by tests covering the YouTube client, TrendRadar service behaviour and FastAPI endpoints.




## DD-002: Separate Popularity from Trend Growth

**Status:** Accepted

### Context
A video's total views indicate accumulated popularity, but do not independently establish whether its topic is growing.

A video with a large number of views may be old, while a newer video may have accumulated views more quickly.

### Decision
TrendRadar will distinguish three concepts:

1. Popularity: public metrics such as views, likes and comments.
2. Performance indicators: average views per day since publication and engagement rate.
3. Trend growth: changes in performance across historical observations.

The first release will calculate popularity and performance indicators from available public data. Trend growth will require historical snapshots and will not be claimed from a single API response.

### Metric definitions

- Average views per day = total views / elapsed days since publication.
- Engagement rate (%) = ((likes + comments) / views) * 100.

If the required data is missing, invalid or insufficient, the relevant metric will be null rather than fabricated.

### Consequences
- Users can distinguish accumulated popularity from average historical performance.
- Metrics remain explainable and testable.
- Historical data collection will be required before making trend-growth claims.

### Limitations
Average views per day is a lifetime average, not current daily view velocity. Engagement rates may not be comparable across all video formats, audiences or publication ages.

### Verification
Unit tests will cover valid calculations, missing metrics, zero views, invalid publication dates and future publication dates.





## DD-003: Research Priority Scoring

**Status:** Accepted — Initial scoring model

### Context
TrendRadar retrieves multiple popular videos. Ranking by total views alone may prioritise older videos and overlook newer videos with strong average performance and engagement.

### Decision
TrendRadar will use a transparent Research Priority Score (RPS) to help users prioritise videos for further research.

### Initial weights
- Average views per day: 40%
- Engagement rate: 30%
- Freshness: 20%
- Total views: 10%

### Scoring
Performance and engagement metrics are normalised relative to the retrieved video sample using min-max scaling.

Freshness uses an exponential decay with a 30-day half-life.

Popularity uses relative total-view counts.

The final score ranges from 0 to 100. Missing metrics are excluded and the remaining weights are proportionally adjusted.

### Interpretation
RPS is a research prioritisation score. It is not a viral probability, niche-demand measurement, monetisation prediction or YouTube algorithm score.

Scores are relative to the retrieved sample and can change when the sample changes.

### Limitations
- The API's popular-video results are not a complete representation of all videos in a niche.
- A sample-relative score cannot establish market demand.
- Average views per day is not current view velocity.
- Engagement varies across formats, audiences and publication ages.
- The initial weights require future validation.

### Verification
Unit tests cover normalisation, ties, missing metrics, score bounds, freshness decay and ranking order.


## DD-004: Historical Trend Tracking with SQLite

**Status:** Accepted

### Context
TrendRadar currently retrieves public video metrics as a single observation. A single observation cannot establish whether video performance is accelerating or declining.

### Decision
TrendRadar will persist periodic observations of video metrics using SQLite.

Each observation records:
- Video ID
- Observation timestamp
- Region
- Video title
- Channel title
- Publication timestamp
- Views
- Likes
- Comments

TrendRadar will compare the latest observation against the previous observation for the same video.

### Derived metrics
- View delta: current views minus previous views.
- Views per day between observations: view delta divided by elapsed time in days.
- View growth percentage: view delta divided by previous views, multiplied by 100.

### Data integrity
- Observations are immutable historical records.
- A video may have multiple observations.
- Historical observations must not be overwritten when new observations arrive.
- A video with no previous observation will have no historical growth metrics.
- A zero previous view count prevents percentage growth calculation.

### Storage
SQLite is selected for the MVP because it is included in Python's standard library and supports local persistent storage.

### Limitations
Historical metrics depend on how frequently TrendRadar captures data. A single observation does not provide historical growth. Growth between observations is not equivalent to real-time velocity.

### Verification
Tests will cover persistence, previous observation retrieval, growth calculations, missing history, zero views and time intervals.



## DD-005: Historical Trend Analysis

**Status:** Accepted

### Context
TrendRadar stores video observations over time. Historical records allow us to measure changes in views rather than relying exclusively on cumulative totals.

### Decision
A separate trend-analysis module will calculate historical performance metrics using the current observation and previous observations.

### Metrics
- Views delta = current views minus previous views.
- Interval views/day = views delta divided by elapsed interval days.
- Growth percentage = views delta divided by previous views, multiplied by 100.
- Acceleration = current interval views/day minus previous interval views/day.

### Trend classifications
- new: insufficient historical observations.
- growing: views increased.
- stable: views remained unchanged.
- declining: views decreased.
- accelerating: interval views/day increased compared with the preceding interval.
- decelerating: interval views/day decreased compared with the preceding interval.

### Data integrity
- Missing observations produce unavailable metrics.
- Zero previous views prevent percentage-growth calculation.
- Negative view deltas are preserved instead of silently discarded.
- Observations with zero or negative elapsed time cannot produce interval velocity.
- Acceleration requires at least three observations.

### Limitations
The engine measures changes between recorded snapshots, not real-time performance. Sampling frequency affects interpretation.

### Verification
Unit tests cover missing history, positive and negative view changes, zero views, elapsed-time calculations, stable performance, acceleration and deceleration.


============================================================================================================================================== 

## DD-006: API-Triggered Snapshot Collection

**Status:** Accepted — MVP

### Context
The historical trend tracking engine can save and analyse observations, but it is not yet connected to the TrendRadar API workflow.

### Decision
When TrendRadar retrieves country-specific popular videos successfully, it will record a historical observation for each returned video.

The API will enrich each video with its historical trend metrics when previous observations are available.

### Collection trigger
Snapshots are recorded when a successful country-trends API request retrieves video data.

### Consequences
- Historical collection begins through API usage.
- Users can receive trend metrics without manually recording observations.
- Repeated requests can generate additional snapshots.
- Data collection frequency depends on user requests.

### Limitations
This is not continuous monitoring.
No snapshot is collected when the API is not requested.
Trend calculations are only as reliable as the observation intervals and collected history.

### Future improvement
Introduce scheduled collection and configurable observation frequency.

=============================================================================================================================================

## DD-007: Snapshot Collection Cooldown

**Status:** Implemented — verified by automated tests

### Context

Trend observations are collected when the Trends API is requested. Repeated requests within short periods could generate unnecessary snapshots and result in unreliable historical trend calculations.

### Decision

A configurable minimum collection interval is applied per video.

Initial default:

- 60 minutes

The decision is implemented in `TrendTrackingService` because it is collection policy, not persistence and not an API-routing concern. The SQLite repository remains responsible only for storing and retrieving observations.

### Rules

- Videos without historical observations are recorded immediately.
- Observations inside the cooldown period are not recorded.
- Observations at or after the cooldown boundary are recorded.
- Existing observations are preserved and are never overwritten.
- Historical analysis continues using available snapshots, even when a new snapshot is skipped.
- Out-of-order observations are rejected safely. An observation timestamp equal to or earlier than the latest stored observation is not recorded.
- Timestamps are normalised to UTC. `Z`, `+00:00` and naive timestamps are handled without timezone comparison errors. Naive timestamps are treated as UTC, matching the existing repository convention.

### Consequences

- Repeated API requests no longer create redundant historical records for the same video.
- Historical analysis protects existing observations from misleading out-of-order data.
- Snapshot frequency is controlled by the tracking service rather than by callers or the database layer.

### Configuration

`TrendTrackingService` accepts an optional `min_collection_interval` as a `datetime.timedelta`. The default is `timedelta(minutes=60)`.

### Limitations

Snapshots remain triggered by API requests. This feature does not introduce a scheduler or automatic background monitoring.

### Verification

Tests cover first observations, cooldown protection, the 60-minute boundary, longer intervals, configurable intervals, preserved history, out-of-order timestamps, timezone formats, naive timestamps and continued historical analysis when recording is skipped. An API-level test also verifies repeated requests against a real temporary SQLite repository.
