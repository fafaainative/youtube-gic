import pandas as pd
import streamlit as st

from app.ui.demo_provider import (
    ALL_CATEGORIES,
    COUNTRY_ALL,
    DEMO_CATEGORIES,
    DEMO_COUNTRIES,
    DEMO_FORMATS,
    DemoTrendProvider,
)
from app.ui.formatting import (
    build_video_table,
    format_count,
    format_date,
    format_percent,
    format_score,
)


st.set_page_config(
    page_title="YouTube GIC",
    page_icon="Y",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROVIDER = DemoTrendProvider()

PAGE_CSS = """
<style>
.block-container {
    padding-top: 2.4rem;
    padding-bottom: 3rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label {
    color: #e5e7eb;
}
.hero {
    background: linear-gradient(120deg, #111827 0%, #1e1b4b 100%);
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    color: #f8fafc;
}
.demo-badge {
    display: inline-block;
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
    border-radius: 999px;
    padding: 0.35rem 0.85rem;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.05em;
    margin-bottom: 0.8rem;
}
.section-title {
    margin-top: 1.4rem;
    margin-bottom: 0.6rem;
}
.stMetric {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 0.7rem;
}
</style>
"""


def render_sidebar():
    st.sidebar.markdown("## YouTube GIC")
    st.sidebar.caption("Growth Intelligence for Creators")

    page = st.sidebar.radio(
        "Navigation",
        ("Dashboard", "Trend Radar", "Video Research"),
        key="page",
    )

    st.sidebar.divider()

    country = st.sidebar.selectbox(
        "Country",
        list(DEMO_COUNTRIES),
        format_func=lambda code: DEMO_COUNTRIES[code],
        key="country",
        index=0,
    )

    category = st.sidebar.selectbox(
        "Content category",
        list(DEMO_CATEGORIES),
        format_func=lambda key: DEMO_CATEGORIES[key],
        key="category",
        index=0,
    )

    video_format = st.sidebar.selectbox(
        "Content format",
        DEMO_FORMATS,
        key="video_format",
        index=0,
    )

    st.sidebar.divider()
    st.sidebar.markdown("### Analysis controls")

    limit = st.sidebar.slider(
        "Videos to display",
        min_value=1,
        max_value=30,
        value=12,
        step=1,
        key="limit",
    )

    show_breakdown = st.sidebar.checkbox(
        "Show score breakdown",
        value=False,
        key="show_breakdown",
    )

    if st.sidebar.button("Reset filters", key="reset_filters"):
        for key in (
            "country",
            "category",
            "video_format",
            "limit",
            "show_breakdown",
            "radar_signature",
            "radar_results",
        ):
            st.session_state.pop(key, None)
        st.rerun()

    st.sidebar.info(
        "Demo data only. This page does not call the YouTube API "
        "or require an API key."
    )

    return {
        "page": page,
        "country": country,
        "category": category,
        "format": video_format,
        "limit": limit,
        "show_breakdown": show_breakdown,
    }


def render_header(page):
    st.markdown(
        """
        <div class="hero">
            <h1>YouTube GIC</h1>
            <h3>YouTube Growth Intelligence for Creators</h3>
            <p>Research smarter. Create strategically. Grow globally.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="demo-badge">DEMO MODE — SIMULATED DATA</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Current page: {page}")


def load_videos(filters, message):
    try:
        with st.spinner(message):
            return PROVIDER.get_country_trends(
                country_code=filters["country"],
                category_id=filters["category"],
                limit=filters["limit"],
                video_format=filters["format"],
            )
    except Exception:
        st.error(
            "Trend data could not be loaded. Reset the filters "
            "and try again."
        )
        return []


def render_empty_state():
    st.warning(
        "No simulated videos match these filters. Try another "
        "country, category or format."
    )


def render_summary_metrics(videos):
    engagement_values = [
        video.engagement_rate
        for video in videos
        if video.engagement_rate is not None
    ]
    scores = [
        video.research_priority_score
        for video in videos
        if video.research_priority_score is not None
    ]

    average_engagement = (
        sum(engagement_values) / len(engagement_values)
        if engagement_values
        else None
    )
    highest_score = max(scores) if scores else None
    trending_count = sum(
        1
        for video in videos
        if video.trend_direction == "growing"
    )

    first, second, third, fourth = st.columns(4)

    first.metric("Videos analysed", len(videos), border=True)
    second.metric(
        "Trending videos",
        trending_count,
        help=(
            "Simulated videos with a growing trend direction."
        ),
        border=True,
    )
    third.metric(
        "Average engagement rate",
        format_percent(average_engagement),
        help=(
            "Average of likes plus comments divided by views "
            "across the simulated results."
        ),
        border=True,
    )
    fourth.metric(
        "Highest research priority score",
        format_score(highest_score),
        help=(
            "Highest sample-relative score in the current "
            "simulated results."
        ),
        border=True,
    )


def chart_frame(videos):
    return pd.DataFrame(
        [
            {
                "Video": video.title,
                "Research Priority Score": (
                    video.research_priority_score
                ),
                "Views": video.view_count,
                "Engagement %": video.engagement_rate,
                "Trend": video.trend_direction or "unknown",
            }
            for video in videos
        ]
    )


def render_charts(videos):
    frame = chart_frame(videos)

    st.markdown(
        '<div class="section-title"><h3>Visual insights</h3></div>',
        unsafe_allow_html=True,
    )

    ranking_column, views_column = st.columns(2)

    with ranking_column:
        st.markdown("#### Research priority ranking")
        st.bar_chart(
            frame.head(10),
            x="Video",
            y="Research Priority Score",
            horizontal=True,
            sort=False,
            color="#6C63FF",
            height=340,
            width="stretch",
        )

    with views_column:
        st.markdown("#### Views comparison")
        st.bar_chart(
            frame.head(10),
            x="Video",
            y="Views",
            horizontal=True,
            sort=False,
            color="#2563EB",
            height=340,
            width="stretch",
        )

    engagement_column, trend_column = st.columns(2)

    with engagement_column:
        st.markdown("#### Engagement comparison")
        st.bar_chart(
            frame.head(10),
            x="Video",
            y="Engagement %",
            sort=False,
            color="#0891B2",
            height=300,
            width="stretch",
        )

    with trend_column:
        st.markdown("#### Trend distribution")
        trend_counts = (
            frame["Trend"]
            .value_counts()
            .rename_axis("Trend")
            .reset_index(name="Videos")
        )
        st.bar_chart(
            trend_counts,
            x="Trend",
            y="Videos",
            sort=False,
            color="#059669",
            height=300,
            width="stretch",
        )


def render_video_table(videos, heading="Top Research Opportunities"):
    st.markdown(
        f'<div class="section-title"><h3>{heading}</h3></div>',
        unsafe_allow_html=True,
    )

    rows = build_video_table(videos, PROVIDER)

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        height=min(560, 80 + len(rows) * 38),
    )

    st.caption(
        "Research Priority Scores are relative to the simulated "
        "sample shown. They are not viral predictions."
    )


def render_dashboard(filters):
    st.header("Dashboard overview")

    videos = load_videos(
        filters,
        "Loading simulated Trend Radar data...",
    )

    if not videos:
        render_empty_state()
        return

    render_summary_metrics(videos)
    render_charts(videos)
    render_video_table(videos)


def render_trend_radar(filters):
    st.header("Trend Radar")
    st.caption(
        "Choose filters in the sidebar, then run the simulated "
        "analysis. No API credentials are used."
    )

    signature = (
        filters["country"],
        filters["category"],
        filters["format"],
        filters["limit"],
    )

    if (
        st.session_state.get("radar_signature") != signature
    ):
        st.session_state["radar_results"] = []

    if st.button("Analyse Trends", type="primary"):
        results = load_videos(
            filters,
            "Analysing simulated trends...",
        )
        st.session_state["radar_results"] = results
        st.session_state["radar_signature"] = signature

    results = st.session_state.get("radar_results", [])

    if not results:
        if (
            st.session_state.get("radar_signature")
            == signature
        ):
            render_empty_state()
        else:
            st.info(
                "No analysis has been run for these filters yet. "
                "Click Analyse Trends to see simulated results."
            )
        return

    render_summary_metrics(results)
    render_charts(results)
    render_video_table(results, heading="Trend Radar results")

    with st.expander("Raw trend fields"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Video": video.title,
                        "Trend direction": (
                            video.trend_direction or "—"
                        ),
                        "Momentum": video.momentum or "—",
                        "Views delta": format_count(
                            video.views_delta
                        ),
                        "Growth %": (
                            f"{video.views_growth_percent:.2f}%"
                            if video.views_growth_percent
                            is not None
                            else "—"
                        ),
                    }
                    for video in results
                ]
            ),
            hide_index=True,
            width="stretch",
        )


def render_video_research(filters):
    st.header("Video Research Details")

    videos = load_videos(
        filters,
        "Loading videos for research...",
    )

    if not videos:
        render_empty_state()
        return

    videos_by_id = {
        video.video_id: video for video in videos
    }
    selected_id = st.selectbox(
        "Select a video",
        list(videos_by_id),
        format_func=lambda video_id: (
            f"{videos_by_id[video_id].title} — "
            f"{videos_by_id[video_id].channel_title}"
        ),
        key="research_video",
    )
    video = videos_by_id[selected_id]

    st.subheader(video.title)
    st.caption(
        f"{video.channel_title} | Simulated video ID: "
        f"{video.video_id}"
    )

    first, second, third, fourth = st.columns(4)

    first.metric("Views", format_count(video.view_count), border=True)
    second.metric(
        "Engagement",
        format_percent(video.engagement_rate),
        border=True,
    )
    third.metric(
        "Average views/day",
        format_count(video.average_views_per_day),
        border=True,
    )
    fourth.metric(
        "Research Priority Score",
        format_score(video.research_priority_score),
        border=True,
    )

    details_column, trend_column = st.columns(2)

    with details_column:
        st.markdown("#### Video details")
        st.write(f"**Channel:** {video.channel_title}")
        st.write(
            "**Publication date:** "
            f"{format_date(video.published_at)}"
        )
        st.write(
            "**Category:** "
            f"{PROVIDER.get_video_category(video.video_id) or '—'}"
        )
        st.write(
            "**Format:** "
            f"{PROVIDER.get_video_format(video.video_id) or '—'}"
        )
        st.write(
            "**Likes:** "
            f"{format_count(video.like_count)}"
        )
        st.write(
            "**Comments:** "
            f"{format_count(video.comment_count)}"
        )

    with trend_column:
        st.markdown("#### Trend assessment")
        st.write(
            "**Trend direction:** "
            f"{video.trend_direction or '—'}"
        )
        st.write(f"**Momentum:** {video.momentum or '—'}")
        st.write(
            "**Views delta:** "
            f"{format_count(video.views_delta)}"
        )
        st.write(
            "**Views growth:** "
            f"{format_percent(video.views_growth_percent)}"
        )

    st.markdown(
        '<div class="section-title">'
        "<h3>What the Research Priority Score means</h3>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.info(
        "The Research Priority Score is a 0 to 100 relative "
        "shortlist score. It combines average views per day, "
        "engagement rate, freshness and total views within the "
        "current sample. It helps decide what to research next. "
        "It is not a prediction of viral success, a measure of "
        "market demand or a YouTube algorithm score."
    )

    if filters["show_breakdown"] and video.score_breakdown:
        st.markdown("#### Score breakdown")
        breakdown_rows = [
            {
                "Component": name.replace("_", " ").title(),
                "Sample score": format_score(value),
            }
            for name, value in video.score_breakdown.items()
        ]
        st.dataframe(
            pd.DataFrame(breakdown_rows),
            hide_index=True,
            width="stretch",
        )

    st.markdown(
        '<div class="section-title">'
        "<h3>Historical observations (simulated)</h3>"
        "</div>",
        unsafe_allow_html=True,
    )

    history = PROVIDER.get_video_history(video.video_id)

    if not history:
        st.info(
            "No simulated historical observations are available "
            "for this video."
        )
        return

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Observed at": format_date(
                        snapshot["observed_at"]
                    ),
                    "Views": format_count(
                        snapshot["view_count"]
                    ),
                    "Likes": format_count(
                        snapshot["like_count"]
                    ),
                    "Comments": format_count(
                        snapshot["comment_count"]
                    ),
                }
                for snapshot in history
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    analysis = PROVIDER.get_trend_analysis(video.video_id)

    st.caption(
        "These observations are generated for the demo. "
        f"Analysis: {analysis['trend_direction']} / "
        f"{analysis['momentum']}."
    )


def main():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    filters = render_sidebar()
    render_header(filters["page"])

    if filters["page"] == "Dashboard":
        render_dashboard(filters)
    elif filters["page"] == "Trend Radar":
        render_trend_radar(filters)
    else:
        render_video_research(filters)


if __name__ == "__main__":
    main()
