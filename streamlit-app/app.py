import pandas as pd
import requests
import streamlit as st

API_URL = "https://viprksu7y3.execute-api.ap-south-1.amazonaws.com/copilot"

st.set_page_config(
    page_title="PropelNOI AI Copilot",
    page_icon="🏢",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

html, body, [class*="css"] {
    font-size: 12px;
}

.dashboard-subheader {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 0.35rem;
}

.small-note {
    font-size: 12px;
    color: #6b7280;
}

.try-card {
    padding: 0.9rem;
    border-radius: 14px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    margin-bottom: 0.7rem;
}

.section-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 0.35rem;
}
</style>
""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []


@st.cache_data(ttl=300, show_spinner=False)
def query_api(question: str, include_details: bool = False):
    response = requests.post(
        API_URL,
        json={
            "question": question,
            "include_details": include_details,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


DASHBOARD_CONFIGS = {
    "NOI Forecast Trend": {
        "question": "Show the top 15 properties by forecast NOI.",
        "chart": "noi_line",
        "help": "Shows the latest forecast month top 15 properties by predicted NOI.",
    },
    "Portfolio NOI KPI": {
        "question": "What is the total predicted portfolio NOI?",
        "chart": "metric",
        "help": "Shows the total expected NOI across the portfolio.",
    },
    "Market Rent Gap Analysis": {
        "question": "Show the latest month top 15 properties by rent gap with current and market rent.",
        "chart": "market_rent_combo",
        "help": "Shows the latest month 15 properties with current portfolio rent, predicted market rent, and rent gap.",
    },
    "Rent Gap Impact": {
        "question": "Show top 15 under-rented properties.",
        "chart": "rent_gap_bar",
        "help": "Highlights the top rent-gap opportunities.",
    },
}

TRY_QUESTIONS = {
    "NOI Forecasting": [
        "What is the NOI forecast for property P00460?",
        "Show the top 10 properties by forecast NOI.",
    ],
    "Market Rent Prediction": [
        "Which properties are under-rented in Boston?",
        "Which properties are over-rented in Chicago?",
    ],
    "Maintenance Risk Detection": [
        "Show the maintenance risk distribution across the portfolio.",
        "Which properties are high-risk for maintenance?",
    ],
}


with st.sidebar:
    st.markdown("## 🏢 PropelNOI")
    page = st.radio("Navigation", ["Copilot", "Dashboards"], index=0)
    st.markdown("---")
    st.markdown("### Capabilities")
    st.markdown(
        """
- Rent optimization insights
- NOI forecast lookup
- Portfolio KPI views
- Maintenance risk review
        """
    )


def to_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="ignore")
    return out


def extract_final_business_insight(answer_text: str) -> str:
    if not answer_text:
        return ""
    lines = [line.strip() for line in answer_text.splitlines() if line.strip()]
    for line in reversed(lines):
        if "business insight:" in line.lower():
            return line
    return lines[-1] if lines else ""


def render_try_questions():
    st.markdown("### Try these questions")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
<div class="try-card">
    <div class="section-title">NOI Forecasting</div>
    <div class="small-note">Sample questions for forecast horizon, property outlook, and ranking.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        for q in TRY_QUESTIONS["NOI Forecasting"]:
            if st.button(q, key=f"try_{q}", use_container_width=True):
                st.session_state["prefill_question"] = q

    with c2:
        st.markdown(
            """
<div class="try-card">
    <div class="section-title">Market Rent Prediction</div>
    <div class="small-note">Sample questions for under-rented and over-rented opportunity detection.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        for q in TRY_QUESTIONS["Market Rent Prediction"]:
            if st.button(q, key=f"try_{q}", use_container_width=True):
                st.session_state["prefill_question"] = q

    with c3:
        st.markdown(
            """
<div class="try-card">
    <div class="section-title">Maintenance Risk Detection</div>
    <div class="small-note">Sample questions for risk distribution and high-risk asset prioritization.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        for q in TRY_QUESTIONS["Maintenance Risk Detection"]:
            if st.button(q, key=f"try_{q}", use_container_width=True):
                st.session_state["prefill_question"] = q


def render_metric_dashboard(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    if "total_predicted_noi" not in df.columns:
        st.warning("Expected KPI field not found.")
        return

    series = pd.to_numeric(df["total_predicted_noi"], errors="coerce").dropna()
    if series.empty:
        st.warning("No KPI value returned.")
        return

    st.metric("Portfolio NOI KPI", f"${series.iloc[0]:,.0f}")


def render_noi_forecast_trend(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    needed = {"property_id", "predicted_noi"}
    if not needed.issubset(df.columns):
        st.warning("Expected columns not found for NOI Forecast Trend dashboard.")
        return

    chart_df = df[["property_id", "predicted_noi"]].copy()
    chart_df["predicted_noi"] = pd.to_numeric(chart_df["predicted_noi"], errors="coerce")
    chart_df = chart_df.dropna().head(15)

    if chart_df.empty:
        st.warning("No valid predicted NOI values returned.")
        return

    chart_df = chart_df.set_index("property_id")
    st.line_chart(chart_df)


def render_market_rent_gap_analysis(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    needed = {"property_id", "current_portfolio_rent", "predicted_market_rent", "rent_gap"}
    if not needed.issubset(df.columns):
        st.warning("Expected columns not found for Market Rent Gap Analysis dashboard.")
        return

    chart_df = df[["property_id", "current_portfolio_rent", "predicted_market_rent", "rent_gap"]].copy()
    chart_df["current_portfolio_rent"] = pd.to_numeric(chart_df["current_portfolio_rent"], errors="coerce")
    chart_df["predicted_market_rent"] = pd.to_numeric(chart_df["predicted_market_rent"], errors="coerce")
    chart_df["rent_gap"] = pd.to_numeric(chart_df["rent_gap"], errors="coerce")
    chart_df = chart_df.dropna().head(15)

    if chart_df.empty:
        st.warning("No valid rent comparison values returned.")
        return

    st.bar_chart(
        chart_df[["property_id", "current_portfolio_rent", "predicted_market_rent"]].set_index("property_id")
    )
    st.line_chart(
        chart_df[["property_id", "rent_gap"]].set_index("property_id")
    )


def render_rent_gap_impact(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    needed = {"property_id", "rent_gap"}
    if not needed.issubset(df.columns):
        st.warning("Expected columns not found for Rent Gap Impact dashboard.")
        return

    chart_df = df[["property_id", "rent_gap"]].copy()
    chart_df["rent_gap"] = pd.to_numeric(chart_df["rent_gap"], errors="coerce")
    chart_df = chart_df.dropna().head(15)

    if chart_df.empty:
        st.warning("No valid rent gap values returned.")
        return

    st.bar_chart(chart_df.set_index("property_id"))


if page == "Copilot":
    st.title("🏢 PropelNOI AI Copilot")
    st.caption("Ask natural-language questions about rent optimization, NOI forecasts, and portfolio insights.")

    render_try_questions()
    st.markdown("---")

    default_q = st.session_state.pop("prefill_question", "")
    question = st.chat_input("Ask a question about your portfolio...")
    if default_q and not question:
        question = default_q

    if question:
        st.session_state.history.append({"role": "user", "text": question})

        try:
            with st.spinner("Analyzing portfolio data..."):
                payload = query_api(question, include_details=False)

            st.session_state.history.append(
                {
                    "role": "assistant",
                    "text": payload.get("answer", "No answer returned."),
                }
            )
        except Exception as exc:
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "text": f"Error calling API: {exc}",
                }
            )

    for item in st.session_state.history:
        if item["role"] == "user":
            with st.chat_message("user"):
                st.write(item["text"])
        else:
            with st.chat_message("assistant"):
                st.markdown(item["text"])

    if not st.session_state.history:
        st.info("Ask a question to see AI insights.")

else:
    st.title("📊 PropelNOI Dashboards")
    st.caption("Prebuilt dashboard views for NOI forecasting and market rent analysis.")

    dashboard_name = st.selectbox("Choose a dashboard", list(DASHBOARD_CONFIGS.keys()))
    config = DASHBOARD_CONFIGS[dashboard_name]

    st.markdown(
        f'<div class="dashboard-subheader">{dashboard_name}</div>',
        unsafe_allow_html=True,
    )
    st.write(config["help"])

    try:
        with st.spinner("Loading dashboard..."):
            payload = query_api(config["question"], include_details=True)

        insight_text = payload.get("answer", "")
        final_insight = extract_final_business_insight(insight_text)

        if final_insight:
            st.markdown("#### Business Insight")
            st.markdown(final_insight)

        if dashboard_name == "NOI Forecast Trend":
            render_noi_forecast_trend(payload)
        elif dashboard_name == "Portfolio NOI KPI":
            render_metric_dashboard(payload)
        elif dashboard_name == "Market Rent Gap Analysis":
            render_market_rent_gap_analysis(payload)
        elif dashboard_name == "Rent Gap Impact":
            render_rent_gap_impact(payload)
        else:
            st.warning("Unsupported dashboard configuration.")

    except Exception as exc:
        st.error(f"Unable to load dashboard: {exc}")
