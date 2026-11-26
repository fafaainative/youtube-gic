from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "streamlit_app.py"
)


def load_app():
    return AppTest.from_file(
        str(APP_PATH),
        default_timeout=20,
    ).run()


def test_dashboard_renders_summary_metrics_and_demo_label():
    app_test = load_app()

    assert not app_test.exception
    assert any(
        "DEMO MODE — SIMULATED DATA" in element.value
        for element in app_test.markdown
    )
    assert [
        metric.label for metric in app_test.metric
    ] == [
        "Videos analysed",
        "Trending videos",
        "Average engagement rate",
        "Highest research priority score",
    ]
    assert len(app_test.dataframe) == 1


def test_trend_radar_button_and_research_page_render():
    app_test = load_app()

    app_test.radio[0].set_value("Trend Radar").run()

    analyse_button = next(
        button
        for button in app_test.button
        if button.label == "Analyse Trends"
    )
    analyse_button.click().run()

    assert not app_test.exception
    assert len(app_test.dataframe) >= 2

    app_test.radio[0].set_value("Video Research").run()

    assert not app_test.exception
    assert any(
        metric.label == "Research Priority Score"
        for metric in app_test.metric
    )


def test_empty_filter_state_is_reported():
    app_test = load_app()

    app_test.selectbox[1].set_value("20").run()
    app_test.selectbox[2].set_value("Shorts").run()
    app_test.radio[0].set_value("Trend Radar").run()

    analyse_button = next(
        button
        for button in app_test.button
        if button.label == "Analyse Trends"
    )
    analyse_button.click().run()

    assert not app_test.exception
    assert any(
        "No simulated videos match" in warning.value
        for warning in app_test.warning
    )
