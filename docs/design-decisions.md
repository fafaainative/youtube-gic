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


