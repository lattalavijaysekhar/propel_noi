import pandas as pd
import requests
import streamlit as st
import matplotlib.pyplot as plt

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

/* Global base font */
html, body, [class*="css"] {
    font-size: 12px;
}

/* Dashboard title/subheader */
.dashboard-subheader {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 0.35rem;
}

/* General helper text */
.small-note {
    font-size: 12px;
    color: #6b7280;
}

/* Try question cards */
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

/* Snapshot cards */
.snapshot-box {
    padding: 0.8rem 1rem;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid #e6ebf2;
    min-height: 90px;
}
.snapshot-label {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 0.25rem;
}
.snapshot-value {
    font-size: 26px;
    font-weight: 600;
    color: #1f2937;
}

/* Query context */
.query-context {
    padding: 0.8rem 1rem;
    border-radius: 14px;
    background: #fbfcfe;
    border: 1px solid #e6ebf2;
    font-size: 12px;
}

/* Reduce white space around pyplot charts */
[data-testid="stVerticalBlock"] .element-container:has(canvas) {
    margin-bottom: 0.25rem;
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
        "question": "Show top 15 highest NOI properties",
        "chart": "noi_line",
        "help": "Shows the latest forecast month 15 properties by predicted NOI.",
    },
    "Portfolio NOI KPI": {
        "question": "What is the total predicted portfolio NOI?",
        "chart": "metric",
        "help": "Shows the overall predicted NOI across the forecast portfolio.",
    },
    "Market Rent Gap Analysis": {
        "question": "Show latest month top 15 properties by rent gap",
        "chart": "market_rent_combo",
        "help": "Shows the latest month 15 properties with current portfolio rent, predicted market rent, and rent gap.",
    },
    "Rent Gap Impact": {
        "question": "Which properties are under-rented in Boston?",
        "chart": "rent_gap_bar",
        "help": "Highlights rent gap opportunities from the returned result set.",
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


def pretty_label(value: str) -> str:
    if not value:
        return "N/A"
    return value.replace("_", " ").title()


def to_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="ignore")
    return out


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


def render_response_meta(item: dict):
    total_count = item.get("total_count", 0)
    row_count = item.get("row_count", 0)
    time_mode = pretty_label(item.get("time_mode", ""))
    mode = pretty_label(item.get("mode", ""))

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
<div class="snapshot-box">
    <div class="snapshot-label">Rows Returned</div>
    <div class="snapshot-value">{row_count}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
<div class="snapshot-box">
    <div class="snapshot-label">Total Matches</div>
    <div class="snapshot-value">{total_count}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("#### Query Context")
    st.markdown(
        f"""
<div class="query-context">
    <div><b>Time Mode:</b> {time_mode}</div>
    <div><b>Mode:</b> {mode}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_metric_dashboard(payload: dict):
    data = payload.get("data", [])
    df = pd.DataFrame(data)

    if df.empty:
        total_from_answer = payload.get("total_count", 0)
        st.metric("Portfolio NOI KPI", f"{total_from_answer:,}" if total_from_answer else "N/A")
        return

    df = to_numeric_df(df)

    value = None
    if "total_predicted_noi" in df.columns:
        series = pd.to_numeric(df["total_predicted_noi"], errors="coerce").dropna()
        if not series.empty:
            value = series.iloc[0]

    if value is None:
        st.warning("No KPI value returned for this dashboard.")
    else:
        st.metric("Portfolio NOI KPI", f"${value:,.0f}")


def render_noi_forecast_trend(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    required = {"property_id", "predicted_noi"}
    if not required.issubset(df.columns):
        st.warning("Expected columns not found for NOI Forecast Trend dashboard.")
        return

    chart_df = df[["property_id", "predicted_noi"]].copy()
    chart_df["predicted_noi"] = pd.to_numeric(chart_df["predicted_noi"], errors="coerce")
    chart_df = chart_df.dropna(subset=["predicted_noi"])
    chart_df = chart_df.head(15)

    if chart_df.empty:
        st.warning("No valid predicted NOI values returned.")
        return

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(chart_df["property_id"], chart_df["predicted_noi"], marker="o")
    ax.set_xlabel("Property ID")
    ax.set_ylabel("Predicted NOI")
    ax.set_title("Latest Forecast Month - Top 15 Properties by Predicted NOI", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def render_market_rent_gap_analysis(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    required = {"property_id", "current_portfolio_rent", "predicted_market_rent", "rent_gap"}
    if not required.issubset(df.columns):
        st.warning("Expected columns not found for Market Rent Gap Analysis dashboard.")
        return

    chart_df = df[["property_id", "current_portfolio_rent", "predicted_market_rent", "rent_gap"]].copy()
    chart_df["current_portfolio_rent"] = pd.to_numeric(chart_df["current_portfolio_rent"], errors="coerce")
    chart_df["predicted_market_rent"] = pd.to_numeric(chart_df["predicted_market_rent"], errors="coerce")
    chart_df["rent_gap"] = pd.to_numeric(chart_df["rent_gap"], errors="coerce")
    chart_df = chart_df.dropna()
    chart_df = chart_df.head(15)

    if chart_df.empty:
        st.warning("No valid rent comparison values returned.")
        return

    fig, ax1 = plt.subplots(figsize=(13, 5.2))

    x = range(len(chart_df))
    width = 0.38

    ax1.bar(
        [i - width / 2 for i in x],
        chart_df["current_portfolio_rent"],
        width=width,
        label="Current Portfolio Rent",
    )
    ax1.bar(
        [i + width / 2 for i in x],
        chart_df["predicted_market_rent"],
        width=width,
        label="Predicted Market Rent",
    )
    ax1.set_ylabel("Rent")
    ax1.set_xlabel("Property ID")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(chart_df["property_id"], rotation=45, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(x, chart_df["rent_gap"], marker="o", label="Rent Gap")
    ax2.set_ylabel("Rent Gap")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

    ax1.set_title("Latest Month - Top 15 Properties Rent Comparison", fontsize=14)
    plt.tight_layout()
    st.pyplot(fig)


def render_rent_gap_impact(payload: dict):
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        st.warning("No data returned for this dashboard.")
        return

    df = to_numeric_df(df)

    required = {"property_id", "rent_gap"}
    if not required.issubset(df.columns):
        st.warning("Expected columns not found for Rent Gap Impact dashboard.")
        return

    chart_df = df[["property_id", "rent_gap"]].copy()
    chart_df["rent_gap"] = pd.to_numeric(chart_df["rent_gap"], errors="coerce")
    chart_df = chart_df.dropna()
    chart_df = chart_df.head(15)

    if chart_df.empty:
        st.warning("No valid rent gap values returned.")
        return

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.bar(chart_df["property_id"], chart_df["rent_gap"])
    ax.set_xlabel("Property ID")
    ax.set_ylabel("Rent Gap")
    ax.set_title("Rent Gap Impact", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


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
                    "sql": payload.get("sql", ""),
                    "count_sql": payload.get("count_sql", ""),
                    "row_count": payload.get("row_count", 0),
                    "total_count": payload.get("total_count", 0),
                    "time_mode": payload.get("time_mode", ""),
                    "mode": payload.get("mode", ""),
                }
            )
        except Exception as exc:
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "text": f"Error calling API: {exc}",
                    "sql": "",
                    "count_sql": "",
                    "row_count": 0,
                    "total_count": 0,
                    "time_mode": "",
                    "mode": "error",
                }
            )

    for item in st.session_state.history:
        if item["role"] == "user":
            with st.chat_message("user"):
                st.write(item["text"])
        else:
            with st.chat_message("assistant"):
                st.markdown(item["text"])
                st.markdown("### Snapshot")
                render_response_meta(item)

                if item.get("sql") or item.get("count_sql"):
                    with st.expander("SQL used"):
                        if item.get("count_sql"):
                            st.markdown("**Count SQL**")
                            st.code(item["count_sql"], language="sql")
                        if item.get("sql"):
                            st.markdown("**Detail SQL**")
                            st.code(item["sql"], language="sql")

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

        if payload.get("answer"):
            st.markdown("#### Business Insight")
            st.markdown(payload["answer"])

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
