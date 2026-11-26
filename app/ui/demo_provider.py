from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.modules.trend_radar.metrics import (
    calculate_average_views_per_day,
    calculate_engagement_rate,
)
from app.modules.trend_radar.ranking import (
    calculate_research_priority_scores,
)
from app.modules.trend_radar.schemas import VideoTrend
from app.modules.trend_radar.trend_analysis import (
    analyze_video_trend,
)


DEMO_AS_OF = datetime(2026, 11, 26, 9, 0, tzinfo=timezone.utc)

ALL_COUNTRIES = "all"
ALL_CATEGORIES = "all"

COUNTRY_ALL = "all"

DEMO_COUNTRIES = {
    COUNTRY_ALL: "All countries",
    "NG": "Nigeria",
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "IN": "India",
    "ZA": "South Africa",
}

DEMO_CATEGORIES = {
    ALL_CATEGORIES: "All categories",
    "1": "Film & Animation",
    "10": "Music",
    "17": "Sports",
    "20": "Gaming",
    "24": "Entertainment",
    "25": "News & Politics",
    "27": "Education",
    "28": "Science & Technology",
}

DEMO_FORMATS = ("All videos", "Shorts", "Long-form")


@dataclass(frozen=True)
class DemoVideoRecord:
    video_id: str
    country_code: str
    category_id: str
    video_format: str
    title: str
    channel_title: str
    published_at: str
    view_count: int
    like_count: int
    comment_count: int
    previous_view_count: int | None = None
    older_view_count: int | None = None


DEMO_CATALOG = (
    DemoVideoRecord(
        "demo_ng_001",
        "NG",
        "24",
        "Long-form",
        "Lagos Street Food: 50 Dishes in One Day",
        "Chuka Eats",
        "2026-11-18T08:00:00Z",
        1280000,
        76000,
        4200,
        1190000,
        1080000,
    ),
    DemoVideoRecord(
        "demo_ng_002",
        "NG",
        "10",
        "Shorts",
        "Afrobeats Dance Challenge in 30 Seconds",
        "Nia Dance",
        "2026-11-22T12:00:00Z",
        890000,
        62000,
        3100,
        830000,
        760000,
    ),
    DemoVideoRecord(
        "demo_ng_003",
        "NG",
        "28",
        "Long-form",
        "Budget Phone Camera Test in Abuja",
        "Tek Vault",
        "2026-11-12T09:00:00Z",
        415000,
        19800,
        1460,
        415000,
        390000,
    ),
    DemoVideoRecord(
        "demo_ng_004",
        "NG",
        "25",
        "Long-form",
        "Which Nigerian Payment App Wins?",
        "Fintech Naija",
        "2026-11-08T07:00:00Z",
        274000,
        12300,
        2810,
        292000,
        310000,
    ),
    DemoVideoRecord(
        "demo_ng_005",
        "NG",
        "27",
        "Shorts",
        "How I Edit Viral Reels on My Phone",
        "Creative Kemi",
        "2026-11-24T14:00:00Z",
        96000,
        8100,
        420,
    ),
    DemoVideoRecord(
        "demo_us_001",
        "US",
        "28",
        "Long-form",
        "I Trained an AI to Edit My Photos",
        "Pixel Lab",
        "2026-11-19T16:00:00Z",
        2150000,
        118000,
        6900,
        1980000,
        1760000,
    ),
    DemoVideoRecord(
        "demo_us_002",
        "US",
        "24",
        "Shorts",
        "30-Second Desk Setup Transformation",
        "Minimal Space",
        "2026-11-23T10:00:00Z",
        1740000,
        129000,
        4300,
        1690000,
        1510000,
    ),
    DemoVideoRecord(
        "demo_us_003",
        "US",
        "10",
        "Long-form",
        "Beginner Guitar: One Chord, One Song",
        "Orbit Music",
        "2026-11-14T11:00:00Z",
        640000,
        41000,
        2200,
        640000,
        610000,
    ),
    DemoVideoRecord(
        "demo_us_004",
        "US",
        "17",
        "Long-form",
        "Trade Deadline: Winners and Losers",
        "Courtside Weekly",
        "2026-11-21T18:00:00Z",
        930000,
        39000,
        9100,
        1010000,
        880000,
    ),
    DemoVideoRecord(
        "demo_us_005",
        "US",
        "27",
        "Shorts",
        "STEM Career Paths Nobody Explains Well",
        "Future Mint",
        "2026-11-20T13:00:00Z",
        310000,
        24500,
        1800,
        280000,
        250000,
    ),
    DemoVideoRecord(
        "demo_gb_001",
        "GB",
        "24",
        "Long-form",
        "London Hidden Bookshops Walk",
        "Slow London",
        "2026-11-17T10:00:00Z",
        510000,
        34000,
        1900,
        480000,
        440000,
    ),
    DemoVideoRecord(
        "demo_gb_002",
        "GB",
        "1",
        "Shorts",
        "Rainy Day Portraits in Manchester",
        "Frame and Light",
        "2026-11-22T15:00:00Z",
        288000,
        22400,
        980,
        275000,
        260000,
    ),
    DemoVideoRecord(
        "demo_gb_003",
        "GB",
        "28",
        "Long-form",
        "UK Broadband Speed Test Challenge",
        "Circuit Yard",
        "2026-11-11T08:00:00Z",
        372000,
        15100,
        2300,
        372000,
        360000,
    ),
    DemoVideoRecord(
        "demo_gb_004",
        "GB",
        "17",
        "Shorts",
        "Premier League Matchday Reactions",
        "Terrace Talk",
        "2026-11-24T17:00:00Z",
        720000,
        41000,
        5600,
        760000,
        690000,
    ),
    DemoVideoRecord(
        "demo_gb_005",
        "GB",
        "20",
        "Long-form",
        "Indie Game Dev: First 30 Days",
        "North Pixel",
        "2026-11-16T09:00:00Z",
        195000,
        17800,
        1340,
        168000,
        142000,
    ),
    DemoVideoRecord(
        "demo_ca_001",
        "CA",
        "24",
        "Long-form",
        "Toronto Night Market Food Tour",
        "Maple Bites",
        "2026-11-20T19:00:00Z",
        680000,
        45200,
        2600,
        630000,
        580000,
    ),
    DemoVideoRecord(
        "demo_ca_002",
        "CA",
        "1",
        "Shorts",
        "Winter Camera Settings in 40 Seconds",
        "North Frame",
        "2026-11-23T12:00:00Z",
        235000,
        19000,
        740,
        225000,
        205000,
    ),
    DemoVideoRecord(
        "demo_ca_003",
        "CA",
        "28",
        "Long-form",
        "Is an Electric Pickup Actually Practical?",
        "Auto North",
        "2026-11-09T10:00:00Z",
        445000,
        18300,
        3200,
        445000,
        430000,
    ),
    DemoVideoRecord(
        "demo_ca_004",
        "CA",
        "24",
        "Shorts",
        "Quebec City Travel Mistakes to Avoid",
        "Wander North",
        "2026-11-15T14:00:00Z",
        318000,
        21100,
        1180,
        340000,
        310000,
    ),
    DemoVideoRecord(
        "demo_ca_005",
        "CA",
        "27",
        "Long-form",
        "Study With Me: 25-Minute Deep Focus",
        "Study Cabin",
        "2026-11-18T07:00:00Z",
        126000,
        11400,
        620,
        110000,
        94000,
    ),
    DemoVideoRecord(
        "demo_in_001",
        "IN",
        "24",
        "Long-form",
        "Pune Street Food Under 500 Rupees",
        "Desi Plate",
        "2026-11-21T08:00:00Z",
        1560000,
        94000,
        5800,
        1420000,
        1280000,
    ),
    DemoVideoRecord(
        "demo_in_002",
        "IN",
        "10",
        "Shorts",
        "Festival Dance Reel Challenge",
        "Nritya Studio",
        "2026-11-24T13:00:00Z",
        1120000,
        88000,
        3900,
        1040000,
        940000,
    ),
    DemoVideoRecord(
        "demo_in_003",
        "IN",
        "27",
        "Long-form",
        "Exam Revision Plan That Actually Works",
        "Study Ghar",
        "2026-11-13T06:00:00Z",
        730000,
        52000,
        4100,
        730000,
        690000,
    ),
    DemoVideoRecord(
        "demo_in_004",
        "IN",
        "28",
        "Shorts",
        "Monsoon Phone Repair Mistakes",
        "Gadget Doctor",
        "2026-11-19T11:00:00Z",
        520000,
        24000,
        3600,
        560000,
        510000,
    ),
    DemoVideoRecord(
        "demo_in_005",
        "IN",
        "17",
        "Shorts",
        "Cricket Last Over: Fan Reactions",
        "Boundary Line",
        "2026-11-22T16:00:00Z",
        890000,
        47000,
        7200,
        810000,
        740000,
    ),
    DemoVideoRecord(
        "demo_za_001",
        "ZA",
        "1",
        "Long-form",
        "Cape Town Sunrise Hike in 4K",
        "Cape Collective",
        "2026-11-18T05:00:00Z",
        340000,
        26800,
        1450,
        310000,
        280000,
    ),
    DemoVideoRecord(
        "demo_za_002",
        "ZA",
        "24",
        "Shorts",
        "Local Streetwear Finds in Johannesburg",
        "Joburg Fit Check",
        "2026-11-23T09:00:00Z",
        410000,
        33500,
        2100,
        390000,
        350000,
    ),
    DemoVideoRecord(
        "demo_za_003",
        "ZA",
        "28",
        "Long-form",
        "Solar Backup Setup Explained",
        "Grid Smart",
        "2026-11-10T08:00:00Z",
        265000,
        12100,
        2900,
        265000,
        250000,
    ),
    DemoVideoRecord(
        "demo_za_004",
        "ZA",
        "17",
        "Long-form",
        "Springboks Matchday Preview",
        "Rugby Room",
        "2026-11-20T12:00:00Z",
        380000,
        19000,
        3300,
        410000,
        370000,
    ),
    DemoVideoRecord(
        "demo_za_005",
        "ZA",
        "10",
        "Shorts",
        "30-Second Amapiano Dance Tutorial",
        "Groove SA",
        "2026-11-25T15:00:00Z",
        175000,
        16200,
        890,
    ),
)


class DemoTrendProvider:
    """Provide deterministic simulated Trend Radar data."""

    def __init__(self, as_of=None):
        self.as_of = as_of or DEMO_AS_OF
        self._records = {
            record.video_id: record for record in DEMO_CATALOG
        }

    def get_country_trends(
        self,
        country_code=COUNTRY_ALL,
        category_id=ALL_CATEGORIES,
        limit=10,
        video_format=DEMO_FORMATS[0],
    ):
        """Return ranked simulated videos for the selected filters."""

        selected_country = country_code or COUNTRY_ALL

        if selected_country.upper() == COUNTRY_ALL.upper():
            country = COUNTRY_ALL
        else:
            country = selected_country.upper()

        category = category_id or ALL_CATEGORIES
        selected_format = (
            video_format if video_format in DEMO_FORMATS
            else DEMO_FORMATS[0]
        )
        count = 10 if limit is None else max(0, int(limit))

        records = [
            record
            for record in DEMO_CATALOG
            if (
                country == COUNTRY_ALL
                or record.country_code == country
            )
            and (
                category == ALL_CATEGORIES
                or record.category_id == category
            )
            and (
                selected_format == DEMO_FORMATS[0]
                or record.video_format == selected_format
            )
        ][:count]

        videos = [
            self._build_video(record) for record in records
        ]

        ranked_videos = calculate_research_priority_scores(
            videos=videos,
            as_of=self.as_of,
        )

        for video in ranked_videos:
            analysis = self.get_trend_analysis(video.video_id)
            for field, value in analysis.items():
                setattr(video, field, value)

        return ranked_videos

    def get_video_history(self, video_id):
        """Return simulated historical observations for a video."""

        record = self._records.get(video_id)

        if record is None:
            return []

        snapshots = [
            self._snapshot(
                record,
                self.as_of,
                record.view_count,
            )
        ]

        if record.previous_view_count is not None:
            snapshots.append(
                self._snapshot(
                    record,
                    self.as_of - timedelta(days=1),
                    record.previous_view_count,
                )
            )

        if record.older_view_count is not None:
            snapshots.append(
                self._snapshot(
                    record,
                    self.as_of - timedelta(days=2),
                    record.older_view_count,
                )
            )

        return snapshots

    def get_trend_analysis(self, video_id):
        """Analyse the simulated history for one video."""

        return analyze_video_trend(
            self.get_video_history(video_id)
        )

    def get_video_category(self, video_id):
        """Return the display name of a video's category."""

        record = self._records.get(video_id)

        if record is None:
            return None

        return DEMO_CATEGORIES.get(record.category_id)

    def get_video_format(self, video_id):
        """Return the selected format of a video."""

        record = self._records.get(video_id)

        if record is None:
            return None

        return record.video_format

    def _snapshot(self, record, observed_at, view_count):
        return {
            "video_id": record.video_id,
            "observed_at": observed_at.isoformat(),
            "region_code": record.country_code,
            "title": record.title,
            "channel_title": record.channel_title,
            "published_at": record.published_at,
            "view_count": view_count,
            "like_count": record.like_count,
            "comment_count": record.comment_count,
        }

    def _build_video(self, record):
        return VideoTrend(
            video_id=record.video_id,
            title=record.title,
            channel_title=record.channel_title,
            published_at=record.published_at,
            country_code=record.country_code,
            video_url=(
                "https://www.youtube.com/watch?v="
                f"{record.video_id}"
            ),
            view_count=record.view_count,
            like_count=record.like_count,
            comment_count=record.comment_count,
            average_views_per_day=(
                calculate_average_views_per_day(
                    view_count=record.view_count,
                    published_at=record.published_at,
                    as_of=self.as_of,
                )
            ),
            engagement_rate=calculate_engagement_rate(
                view_count=record.view_count,
                like_count=record.like_count,
                comment_count=record.comment_count,
            ),
        )
