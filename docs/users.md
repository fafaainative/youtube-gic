# YouTube GIC — User Guide

YouTube GIC stands for YouTube Growth Intelligence for Creators.

Tagline: Research smarter. Create strategically. Grow globally.

This guide explains what the application does today. It does not describe planned features as if they already exist.

## 1. What YouTube GIC is

YouTube GIC is a research and intelligence platform for YouTube creators. It helps you look at public YouTube data in a more structured way so you can decide which videos deserve closer research.

It is a backend API at this stage. There is no web page or mobile app yet.

## 2. What TrendRadar currently does

TrendRadar is the first module being developed.

When you request country trends, TrendRadar currently:

1. Asks the YouTube Data API v3 for videos on the `mostPopular` chart in a country.
2. Converts the returned videos into YouTube GIC's internal format.
3. Calculates simple performance metrics from the public numbers.
4. Gives each video a relative Research Priority Score.
5. Saves a historical observation when the collection rules allow it.
6. Adds historical trend results to the API response.

TrendRadar does not search every video in a niche. It only works with the videos returned by YouTube's `mostPopular` chart for the selected country and optional category.

## 3. Types of information you will see

It is important to know where each number comes from.

- **Verified YouTube data:** view count, like count, comment count, title, channel title and publication time come from the YouTube Data API response.
- **Calculated metrics:** average views per day and engagement rate are calculated by YouTube GIC from YouTube data.
- **Relative ranking scores:** the Research Priority Score is calculated only within the current retrieved sample.
- **Historical observations:** snapshots are records of video statistics saved at a point in time when TrendRadar collected them.
- **Estimates:** YouTube GIC does not currently produce audience estimates or revenue estimates.
- **Recommendations:** the Research Priority Score helps you choose what to research next. It is not a command to copy a video or a promise of results.

## 4. How to start the application

You need Python 3 and a YouTube Data API v3 key.

From the project folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export YOUTUBE_API_KEY="your_youtube_api_key_here"
.venv/bin/python -m uvicorn app.main:app --reload
```

The API will normally be available at `http://127.0.0.1:8000`.

The repository contains `.env.example` as a reminder of the required variable. The application reads the key from the process environment using `YOUTUBE_API_KEY`. It does not automatically read a `.env` file by itself.

## 5. How to configure the YouTube API key

1. Create or use a Google Cloud project.
2. Enable the YouTube Data API v3 for that project.
3. Create an API key.
4. Set the key in your shell before starting the application:

```bash
export YOUTUBE_API_KEY="your_real_key"
```

Do not put a real key into source code or commit it to Git.

If the key is missing or empty, the trends endpoint returns HTTP `503` with the message that the YouTube API key is not configured.

## 6. How to use the trends endpoint

Check that the application is running:

```bash
curl http://127.0.0.1:8000/health
```

Get popular videos for a country:

```bash
curl "http://127.0.0.1:8000/api/v1/trends?region=NG&limit=10"
```

Query options:

- `region`: a two-letter country code. Default is `NG`.
- `limit`: number of videos, from `1` to `50`. Default is `10`.
- `category_id`: optional YouTube video category ID.

Examples:

```bash
curl "http://127.0.0.1:8000/api/v1/trends?region=US&limit=5"
curl "http://127.0.0.1:8000/api/v1/trends?region=GB&category_id=10"
```

An invalid country code or an out-of-range limit returns HTTP `422`. If YouTube rejects the request, the API returns HTTP `502`.

## 7. How country-specific research works

The `region` value is sent to YouTube as the `regionCode`. YouTube returns videos on its `mostPopular` chart for that country.

For example, `region=NG` asks YouTube for the most popular chart in Nigeria. This is not the same as a complete search for all Nigerian creators or all videos about a topic.

A category ID, when supplied, is also passed to YouTube to narrow the chart request.

Use country research to see what YouTube is currently returning for that country's chart, then research the videos manually before making content decisions.

## 8. How to interpret video statistics

The API returns these public fields from YouTube:

- `view_count`: total views reported by YouTube.
- `like_count`: public likes reported by YouTube.
- `comment_count`: public comments reported by YouTube.
- `published_at`: the video's publication timestamp.
- `average_views_per_day`: calculated as total views divided by days since publication.
- `engagement_rate`: calculated as `(likes + comments) / views * 100`.

If YouTube does not provide a value, YouTube GIC may return `null` instead of guessing.

`average_views_per_day` is a lifetime average. It is not the current daily view speed. A very old video can have a low lifetime average even if it is growing quickly right now.

`engagement_rate` can differ between video formats and audiences. It is useful for comparison within the returned sample, not as a universal quality score.

## 9. What the Research Priority Score means

The Research Priority Score, or RPS, is a number from `0` to `100`. It helps you decide which videos in the current response deserve research first.

It combines four parts:

- Average views per day: 40%
- Engagement rate: 30%
- Freshness: 20%
- Total views: 10%

Performance, engagement and total views are compared with the other videos in the same response. Freshness decays over time with a 30-day half-life, so newer videos generally receive a higher freshness component.

If a component is missing, it is left out and the remaining weights are adjusted. Videos are returned from highest score to lowest score.

The RPS is relative to the retrieved sample. If you change the country, category, limit or request time, the scores can change.

The RPS is **not**:

- a prediction of viral success,
- a measure of total market demand,
- a YouTube algorithm score,
- a monetisation forecast,
- proof that a niche is profitable.

Use it as a shortlist tool, then do your own research.

## 10. What historical trend tracking means

A snapshot is one saved observation of a video's public statistics at a particular time. TrendRadar stores snapshots locally in SQLite when a successful trends request returns video data and the collection rules allow it.

Historical analysis compares the most recent stored snapshots:

- `views_delta`: current views minus previous views.
- `interval_days`: time between the two observations, in days.
- `views_per_day_since_last_snapshot`: view change divided by that interval.
- `views_growth_percent`: view change divided by previous views, multiplied by 100.
- `momentum`: compares the latest interval rate with the preceding interval rate when three snapshots exist.

These values describe changes between recorded observations. They are not real-time tracking and they do not show what happened between snapshots.

## 11. What the trend results mean

You may see these `trend_direction` values:

- `new`: there is no previous stored observation to compare with. This does **not** mean the video was recently published.
- `growing`: views increased between the latest two stored observations.
- `stable`: views stayed the same between the latest two stored observations.
- `declining`: views decreased between the latest two stored observations.
- `unknown`: required data or elapsed time was missing or invalid, so TrendRadar cannot calculate a direction.

You may see these `momentum` values:

- `insufficient_history`: fewer than three snapshots are available.
- `accelerating`: the latest interval views per day is higher than the preceding interval.
- `decelerating`: the latest interval views per day is lower than the preceding interval.
- `steady`: the two interval rates are the same.
- `unknown`: the required interval rates could not be calculated.

A growing video is not guaranteed to keep growing. A declining video is not proof that the topic is bad. Always consider publication age, sample size and the collection interval.

## 12. What the snapshot cooldown means

TrendRadar applies a minimum collection interval of **60 minutes per video** by default.

- A video with no history is recorded immediately.
- A request less than 60 minutes after the latest snapshot does not create a new snapshot.
- A request at least 60 minutes after the latest snapshot can create a new snapshot.
- Existing snapshots are never overwritten or deleted by this rule.
- Historical analysis still runs using the snapshots already available.
- If a requested observation time is earlier than or the same as the latest stored observation, it is skipped so history is not misordered.

Developers can change the interval through the tracking service. There is no API query option for it.

## 13. Why repeated requests may not create new observations

The cooldown exists to stop repeated API refreshes from filling the database with nearly identical snapshots. Too many snapshots taken minutes apart would make interval comparisons noisy and less useful.

If you refresh the trends endpoint twice quickly, you will still receive current YouTube statistics and available historical analysis. Only the saved history may stay unchanged.

Snapshots are collected only when the trends API is requested. YouTube GIC does not currently monitor videos in the background or on a schedule.

## 14. How to access a video's history endpoint

Use the video ID returned by the trends endpoint:

```bash
curl "http://127.0.0.1:8000/api/v1/trends/video123/history"
```

The response contains:

- `video_id`: the requested video.
- `snapshot_count`: the number of snapshots returned in this response, up to 30.
- `snapshots`: the most recent stored observations, newest first, up to 30.
- `trend_analysis`: the historical analysis calculated from the stored snapshots.

If the video has no stored observation, the analysis returns `new` with unavailable metrics.

## 15. Current limitations

- There is no user interface or login system.
- There is no scheduler or automatic background monitoring.
- Trends come only from YouTube's `mostPopular` chart for the selected country.
- The retrieved sample is not a complete picture of a niche.
- Lifetime average views per day are not current view velocity.
- The Research Priority Score is sample-relative and experimental.
- Historical accuracy depends on how often snapshots are collected.
- Data is stored in a local SQLite database.
- The API has no authentication layer.
- YouTube API quotas and outages can affect results.
- Fan engagement counts can be hidden by creators, so some values may be missing.

## 16. Troubleshooting

**The trends endpoint returns `503`.**  
The `YOUTUBE_API_KEY` environment variable is missing or empty. Set it and restart the application.

**The trends endpoint returns `422`.**  
Check that `region` is exactly two letters and `limit` is between `1` and `50`.

**The trends endpoint returns `502`.**  
YouTube may have rejected the request, for example because the key is invalid, the API is disabled or the quota is exhausted. Check your Google Cloud API settings.

**The response shows `view_count: null`.**  
YouTube did not return that statistic for the video. YouTube GIC does not invent a value.

**The trend result says `new` every time.**  
Only one snapshot exists for that video, or the cooldown is preventing new snapshots. Wait for the collection interval to pass, then request trends again.

**The snapshot count did not increase after a refresh.**  
This is expected inside the 60-minute cooldown window. The current YouTube numbers and historical analysis are still returned.

**The momentum says `insufficient_history`.**  
Momentum needs at least three snapshots for the same video.

**The API cannot connect locally.**  
Make sure uvicorn is still running and that you are using the correct port. The command above uses the default port `8000`.


 Run .venv/bin/python -m compileall -q app tests, .venv/bin/python -m pytest -v, then verify streamlit run app/streamlit_app.py --server.headless true --server.port 8501 starts and responds over HTTP; finish with git diff --check and git status.