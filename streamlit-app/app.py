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

/* General font sizing */
html, body, [class*="css"] {
    font-size: 12px;
}

/* Dashboard subheaders */
.dashboard-subheader {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 0.35rem;
}

/* Small helper text */
.small-note {
    font-size: 12px;
    color: #6b7280;
}

/* Try-question cards */
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

/* Query context block */
.query-context {
    padding: 0.8rem 1rem;
    border-radius: 14px;
    background: #fbfcfe;
    border: 1px solid #e6ebf2;
    font-size: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []


@st.cache_data(ttl=300, show_spinner=False)
def query_api(question: str):
    response = requests.post(
        API_URL,
        json={
            "question": question,
            "include_details": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


# Updated dashboard list
DASHBOARD_CONFIGS = {
    "NOI Forecast Trend": {
        "question": "Show the latest forecast month top 15 properties with property_id and predicted_noi ordered by predicted_noi descending",
        "chart": "line_single_metric",
        "x": "property_id",
        "y": "predicted_noi",
        "help": "Shows the latest forecast month top 15 properties by predicted NOI.",
    },
    "Portfolio NOI KPI": {
        "question": "What is the total predicted portfolio NOI?",
        "chart": "metric",
        "value": "total_predicted_noi",
        "help": "Total expected NOI across the portfolio.",
    },
    "Market Rent Gap Analysis": {
        "question": "Show the latest month top 15 properties with property_id, current_portfolio_rent, predicted_market_rent, and rent_gap ordered by absolute rent_gap descending",
        "chart": "market_rent_combo",
        "x": "property_id",
        "bar1": "current_portfolio_rent",
        "bar2": "predicted_market_rent",
        "line": "rent_gap",
        "help": "Shows latest month top 15 properties comparing current rent vs predicted market rent, with rent gap overlay.",
    },
    "Rent Gap Impact": {
        "question": "Show latest month top 15 properties with property_id and rent_gap ordered by absolute rent_gap descending",
        "chart": "bar",
        "x": "property_id",
        "y": "rent_gap",
        "help": "Highlights the latest month top 15 rent gap opportunities.",
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
                payload = query_api(question)

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

    st.markdown(f'<div class="dashboard-subheader">{dashboard_name}</div>', unsafe_allow_html=True)
    st.write(config["help"])

    try:
        with st.spinner("Loading dashboard..."):
            payload = query_api(config["question"])

        if payload.get("answer"):
            st.markdown("#### Business Insight")
            st.markdown(payload["answer"])

        df = pd.DataFrame(payload.get("data", []))

        # Fallback: if API does not return data because include_details=False,
        # still try to use fields if present in payload
        if df.empty and "data" in payload and payload["data"]:
            df = pd.DataFrame(payload["data"])

        if df.empty:
            st.warning("No data returned for this dashboard.")
        else:
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="ignore")

            chart_type = config["chart"]

            if chart_type == "metric":
                value_col = config["value"]
                metric_value = None
                if value_col in df.columns:
                    metric_value = pd.to_numeric(df[value_col], errors="coerce").dropna().sum()
                elif len(df.columns) == 1:
                    metric_value = pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna().sum()

                st.metric(dashboard_name, f"${metric_value:,.0f}" if metric_value is not None else "N/A")

            elif chart_type == "line_single_metric":
                x_col = config["x"]
                y_col = config["y"]
                chart_df = df[[x_col, y_col]].copy().set_index(x_col)
                chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
                st.line_chart(chart_df)

            elif chart_type == "bar":
                x_col = config["x"]
                y_col = config["y"]
                chart_df = df[[x_col, y_col]].copy().set_index(x_col)
                chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
                st.bar_chart(chart_df)

            elif chart_type == "market_rent_combo":
                st.markdown("#### Current Portfolio Rent vs Predicted Market Rent")
                chart_df = df[[config["x"], config["bar1"], config["bar2"]]].copy().set_index(config["x"])
                chart_df[config["bar1"]] = pd.to_numeric(chart_df[config["bar1"]], errors="coerce")
                chart_df[config["bar2"]] = pd.to_numeric(chart_df[config["bar2"]], errors="coerce")
                st.bar_chart(chart_df)

                if config["line"] in df.columns:
                    st.markdown("#### Rent Gap Trend")
                    line_df = df[[config["x"], config["line"]]].copy().set_index(config["x"])
                    line_df[config["line"]] = pd.to_numeric(line_df[config["line"]], errors="coerce")
                    st.line_chart(line_df)

    except Exception as exc:
        st.error(f"Unable to load dashboard: {exc}")
