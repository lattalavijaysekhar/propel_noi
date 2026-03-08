import streamlit as st
import requests
import pandas as pd

API_URL = "https://viprksu7y3.execute-api.ap-south-1.amazonaws.com/copilot"

st.set_page_config(
    page_title="PropelNOI AI Copilot",
    page_icon="🏢",
    layout="wide"
)

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.kpi-card {
    padding: 1rem;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid #e6ebf2;
}
.kpi-title {
    font-size: 0.9rem;
    color: #5b6573;
    margin-bottom: 0.25rem;
}
.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #111827;
}
.small-note {
    font-size: 0.85rem;
    color: #6b7280;
}
</style>
""", unsafe_allow_html=True)

# ---------- Session state ----------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🏢 PropelNOI")
    st.markdown("**AI Copilot for Real Estate Portfolio Analytics**")
    st.markdown("---")
    st.markdown("### What this can do")
    st.markdown(
        """
- Rent optimization insights
- NOI forecast lookup
- Portfolio what-if analysis
- Maintenance risk review
        """
    )
    st.markdown("---")
    st.markdown("### Try these questions")
    sample_questions = [
        "Which properties are under-rented in Boston?",
        "Which properties are over-rented in Chicago?",
        "Forecast NOI for property P00047",
        "What if rent increases by 5% in Seattle?"
    ]
    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state["prefill_question"] = q

# ---------- Header ----------
st.title("🏢 PropelNOI AI Copilot")
st.caption("Ask natural-language questions about rent optimization, NOI forecasts, and portfolio insights.")

# ---------- Input ----------
default_q = st.session_state.pop("prefill_question", "")
question = st.chat_input("Ask a question about your portfolio...", key="chat_box")

if default_q and not question:
    question = default_q

# ---------- Call API ----------
if question:
    st.session_state.history.append({
        "role": "user",
        "text": question
    })

    try:
        with st.spinner("Analyzing portfolio data..."):
            resp = requests.post(API_URL, json={"question": question}, timeout=120)
            resp.raise_for_status()
            payload = resp.json()

        answer = payload.get("answer", "No answer returned.")
        data = payload.get("data", [])
        st.session_state.history.append({
            "role": "assistant",
            "text": answer,
            "data": data
        })

    except Exception as e:
        st.session_state.history.append({
            "role": "assistant",
            "text": f"Error calling API: {e}",
            "data": []
        })

# ---------- Render chat ----------
latest_data = []

for item in st.session_state.history:
    if item["role"] == "user":
        with st.chat_message("user"):
            st.write(item["text"])
    else:
        with st.chat_message("assistant"):
            st.write(item["text"])
            data = item.get("data", [])
            if data:
                latest_data = data

# ---------- KPI cards ----------
if latest_data:
    df = pd.DataFrame(latest_data)

    # hide internal columns if present
    drop_cols = [c for c in ["sql", "result_scope_note"] if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    # numeric conversions
    for col in ["rent_gap", "rent_gap_pct", "annual_rent_opportunity", "current_portfolio_rent", "predicted_market_rent"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    total_rows = len(df)
    distinct_properties = df["property_id"].nunique() if "property_id" in df.columns else total_rows

    avg_gap = df["rent_gap"].mean() if "rent_gap" in df.columns else None
    avg_gap_pct = df["rent_gap_pct"].mean() if "rent_gap_pct" in df.columns else None
    total_opportunity = df["annual_rent_opportunity"].sum() if "annual_rent_opportunity" in df.columns else None

    st.markdown("### Snapshot")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Rows Returned</div>
                <div class="kpi-value">{total_rows}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Distinct Properties</div>
                <div class="kpi-value">{distinct_properties}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        avg_gap_display = f"${avg_gap:,.0f}" if avg_gap is not None and pd.notna(avg_gap) else "N/A"
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Average Rent Gap</div>
                <div class="kpi-value">{avg_gap_display}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        if total_opportunity is not None and pd.notna(total_opportunity):
            opp_display = f"${total_opportunity:,.0f}"
        elif avg_gap_pct is not None and pd.notna(avg_gap_pct):
            opp_display = f"{avg_gap_pct:.1%}"
        else:
            opp_display = "N/A"

        title = "Annual Opportunity" if total_opportunity is not None and pd.notna(total_opportunity) else "Average Gap %"

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{opp_display}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### Result Details")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Ask a question to see AI insights and result details.")
