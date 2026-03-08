import streamlit as st
import requests
import pandas as pd

# Replace with your API Gateway endpoint
API_URL = "https://viprksu7y3.execute-api.ap-south-1.amazonaws.com/copilot"

st.set_page_config(
    page_title="PropelNOI AI Copilot",
    page_icon="🏢",
    layout="wide"
)

# -------------------------------------------------------
# Header
# -------------------------------------------------------

st.title("🏢 PropelNOI AI Copilot")
st.markdown(
    "AI-powered portfolio intelligence platform for real estate asset managers"
)

# -------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "NOI Forecast",
        "Market Rent Analysis",
        "Maintenance Risk",
        "AI Copilot"
    ]
)

# -------------------------------------------------------
# Dashboard
# -------------------------------------------------------

if page == "Dashboard":

    st.subheader("Portfolio Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Properties", "150")
    col2.metric("Forecast NOI (Next Year)", "$24.8M")
    col3.metric("High Risk Assets", "12")

    st.markdown("---")

    st.subheader("Portfolio Performance")

    data = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "NOI": [2.1, 2.4, 2.5, 2.7, 2.6, 2.9]
    })

    st.line_chart(data.set_index("Month"))

# -------------------------------------------------------
# NOI Forecast
# -------------------------------------------------------

elif page == "NOI Forecast":

    st.subheader("NOI Forecast")

    property_id = st.selectbox(
        "Select Property",
        ["P001", "P002", "P003", "P004"]
    )

    forecast_data = pd.DataFrame({
        "Month": [
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ],
        "Predicted NOI": [
            2.9, 3.0, 3.1, 3.2, 3.3, 3.4
        ]
    })

    st.line_chart(forecast_data.set_index("Month"))

    st.dataframe(forecast_data)

# -------------------------------------------------------
# Market Rent Analysis
# -------------------------------------------------------

elif page == "Market Rent Analysis":

    st.subheader("Market Rent Gap Analysis")

    data = pd.DataFrame({
        "Property": ["P001", "P002", "P003", "P004"],
        "Current Rent": [22, 24, 21, 26],
        "Market Rent": [25, 26, 23, 27]
    })

    data["Rent Gap"] = data["Market Rent"] - data["Current Rent"]

    st.dataframe(data)

    st.bar_chart(data.set_index("Property")[["Current Rent", "Market Rent"]])

# -------------------------------------------------------
# Maintenance Risk
# -------------------------------------------------------

elif page == "Maintenance Risk":

    st.subheader("Maintenance Risk Predictions")

    risk_data = pd.DataFrame({
        "Property": ["P001", "P002", "P003", "P004"],
        "Asset": ["HVAC", "Elevator", "Boiler", "Lighting"],
        "Risk Score": [0.82, 0.65, 0.74, 0.33]
    })

    st.dataframe(risk_data)

    st.bar_chart(risk_data.set_index("Asset")["Risk Score"])

# -------------------------------------------------------
# AI Copilot
# -------------------------------------------------------

elif page == "AI Copilot":

    st.subheader("AI Portfolio Copilot")

    user_input = st.text_input(
        "Ask a question about the portfolio:"
    )

    if st.button("Ask Copilot"):

        if user_input:

            payload = {
                "question": user_input
            }

            try:

                response = requests.post(API_URL, json=payload)

                if response.status_code == 200:
                    answer = response.json().get("answer", "")
                    st.success(answer)

                else:
                    st.error("Error from API")

            except Exception as e:
                st.error("Failed to connect to AI Copilot API")
