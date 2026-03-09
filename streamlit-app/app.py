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
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.dashboard-card {
    padding: 1rem;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid #e6ebf2;
}
.small-note {
    font-size: 0.85rem;
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
    font-size: 1rem;
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
def query_api(question: str, include_details: bool = False, max_rows: int = 10):
    response = requests.post(
        API_URL,
        json={
            "question": question,
            "include_details": include_details,
            "max_rows": max_rows,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


DASHBOARD_CONFIGS = {
    "NOI Forecast Trend": {
        "question": "Show forecast_month, property_id, predicted_noi from output_noi_forecast_ml for 10 properties ordered by forecast_month",
        "chart": "line",
        "x": "forecast_month",
        "y": "predicted_noi",
        "series": "property_id",
        "help": "Predicted NOI trajectory across future months.",
    },
    "Portfolio NOI KPI": {
        "question": "What is the total predicted portfolio NOI?",
        "chart": "metric",
        "value": "total_predicted_noi",
        "help": "Total expected NOI across the portfolio.",
    },
    "Market Rent Gap Analysis": {
        "question": "Show the latest month market rent comparison with property_id, current_portfolio_rent and predicted_market_rent for the top 15 rent gap opportunities",
        "chart": "bar_compare",
        "x": "property_id",
        "y1": "current_portfolio_rent",
        "y2": "predicted_market_rent",
        "help": "Compares current portfolio rent against predicted market rent.",
    },
    "Rent Gap Impact": {
        "question": "Show latest month rent gap by property_id for top 15 opportunity properties ordered by absolute rent_gap descending",
        "chart": "bar",
        "x": "property_id",
        "y": "rent_gap",
        "help": "Highlights revenue uplift opportunity if rents are aligned to market.",
    },
    "Maintenance Risk Distribution": {
        "question": "Show maintenance risk distribution by risk_level",
        "chart": "bar",
        "x": "risk_level",
        "y": "property_count",
        "help": "Shows the portfolio mix of high, medium, and low risk assets.",
    },
    "High-Risk Assets Table": {
        "question": "Show high-risk maintenance assets with property_id, asset_type, risk_score, risk_level",
        "chart": "table",
        "help": "Lists assets needing immediate maintenance attention.",
    },
    "Maintenance Risk Heatmap": {
        "question": "Show maintenance risk scores by property_id and asset_type",
        "chart": "heatmap",
        "rows": "property_id",
        "cols": "asset_type",
        "values": "risk_score",
        "help": "Quickly identifies critical assets by property and asset type.",
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


def render_dataframe(df: pd.DataFrame):
    working_df = df.copy()
    for col in working_df.columns:
        working_df[col] = pd.to_numeric(working_df[col], errors="ignore")
    st.dataframe(working_df, use_container_width=True)


def render_try_questions():
    st.markdown("### Try these questions")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
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
            f"""
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
            f"""
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
    total_count = item.get("total_count")
    row_count = item.get("row_count")
    time_mode = item.get("time_mode", "")
    mode = item.get("mode", "")

    cols = st.columns(4)
    cols[0].metric("Rows Returned", row_count if row_count is not None else 0)
    cols[1].metric("Total Matches", total_count if total_count is not None else 0)
    cols[2].metric("Time Mode", time_mode if time_mode else "N/A")
    cols[3].metric("Mode", mode if mode else "N/A")


if page == "Copilot":
    st.title("🏢 PropelNOI AI Copilot")
    st.caption("Ask natural-language questions about rent optimization, NOI forecasts, and portfolio insights.")

    top_left, top_right = st.columns([3, 1])
    with top_left:
        show_details = st.toggle("Show result details", value=False)
    with top_right:
        max_rows = st.selectbox("Rows", [5, 10, 20], index=1)

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
                payload = query_api(question, include_details=show_details, max_rows=max_rows)

            st.session_state.history.append(
                {
                    "role": "assistant",
                    "text": payload.get("answer", "No answer returned."),
                    "data": payload.get("data", []),
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
                    "data": [],
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
                st.markdown("#### Snapshot")
                render_response_meta(item)

                if item.get("sql") or item.get("count_sql"):
                    with st.expander("SQL used"):
                        if item.get("count_sql"):
                            st.markdown("**Count SQL**")
                            st.code(item["count_sql"], language="sql")
                        if item.get("sql"):
                            st.markdown("**Detail SQL**")
                            st.code(item["sql"], language="sql")

                if item.get("data"):
                    with st.expander(f"Result details ({item.get('row_count', len(item['data']))} rows)"):
                        render_dataframe(pd.DataFrame(item["data"]))

    if not st.session_state.history:
        st.info("Ask a question to see AI insights and optional result details.")

else:
    st.title("📊 PropelNOI Dashboards")
    st.caption("Prebuilt dashboard views for NOI forecasting, market rent analysis, and maintenance risk monitoring.")

    dashboard_name = st.selectbox("Choose a dashboard", list(DASHBOARD_CONFIGS.keys()))
    config = DASHBOARD_CONFIGS[dashboard_name]

    left, right = st.columns([4, 1])
    with left:
        st.markdown(f"### {dashboard_name}")
        st.write(config["help"])
    with right:
        if st.button("Refresh dashboard", use_container_width=True):
            query_api.clear()

    try:
        with st.spinner("Loading dashboard..."):
            payload = query_api(config["question"], include_details=True, max_rows=50)

        st.markdown(payload.get("answer", ""))

        df = pd.DataFrame(payload.get("data", []))
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
                render_dataframe(df)

            elif chart_type == "line":
                x_col = config["x"]
                y_col = config["y"]
                series_col = config["series"]
                chart_df = df[[x_col, series_col, y_col]].copy()
                chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
                pivot_df = chart_df.pivot_table(index=x_col, columns=series_col, values=y_col, aggfunc="sum")
                st.line_chart(pivot_df)
                render_dataframe(df)

            elif chart_type == "bar_compare":
                x_col = config["x"]
                y1 = config["y1"]
                y2 = config["y2"]
                chart_df = df[[x_col, y1, y2]].copy().set_index(x_col)
                chart_df[y1] = pd.to_numeric(chart_df[y1], errors="coerce")
                chart_df[y2] = pd.to_numeric(chart_df[y2], errors="coerce")
                st.bar_chart(chart_df)
                render_dataframe(df)

            elif chart_type == "bar":
                x_col = config["x"]
                y_col = config["y"]
                chart_df = df[[x_col, y_col]].copy().set_index(x_col)
                chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
                st.bar_chart(chart_df)
                render_dataframe(df)

            elif chart_type == "heatmap":
                pivot_df = df.pivot_table(
                    index=config["rows"],
                    columns=config["cols"],
                    values=config["values"],
                    aggfunc="max",
                )
                st.dataframe(pivot_df, use_container_width=True)
                render_dataframe(df)

            else:
                render_dataframe(df)

    except Exception as exc:
        st.error(f"Unable to load dashboard: {exc}")
