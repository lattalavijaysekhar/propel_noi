
# PropelNOI AI Copilot

AI-powered portfolio intelligence platform for real estate asset managers.

PropelNOI helps portfolio managers forecast **Net Operating Income (NOI)**, detect **market rent gaps**, predict **maintenance risks**, and interact with portfolio data using a **Generative AI Copilot**.

The system integrates **machine learning and generative AI on AWS** to transform traditional reporting dashboards into **predictive decision intelligence**.

---

# Problem Statement

Real estate portfolio managers rely heavily on historical dashboards and manual analysis to monitor asset performance.

However, key decisions require forward-looking insights such as:

- What will **NOI be next year?**
- Which properties are **underpriced compared to market rent?**
- Which assets may **require maintenance soon?**
- What happens if **occupancy changes or costs increase?**

Traditional BI tools cannot answer these questions effectively.

PropelNOI solves this problem using **predictive analytics and generative AI**.

---

# Why AI is Required

AI enables the system to detect patterns hidden within large operational datasets.

Machine learning models help:

- Forecast **future NOI trends**
- Predict **market rent values**
- Detect **maintenance risks before failures occur**

Generative AI enables a **natural language Copilot** that allows users to ask questions and receive intelligent explanations.

This transforms static reporting into **interactive decision intelligence**.

---

# Solution Overview

PropelNOI consists of four core AI services:

### 1. NOI Predictor
Forecasts future Net Operating Income using time-series forecasting.

### 2. Market Rent Harmonizer
Predicts market rent and identifies properties priced below market value.

### 3. Predictive Maintenance Shield
Identifies assets with high probability of maintenance issues.

### 4. AI Copilot
Provides natural language portfolio insights powered by generative AI.

The system is delivered through a **Streamlit SaaS-style interface**.

---

# Architecture Overview

The solution uses a **serverless AWS architecture**.

Data Sources  
→ Amazon S3 Data Lake  
→ AWS Glue ETL Processing  
→ Amazon Athena Query Layer  
→ SageMaker Machine Learning Models  
→ Amazon Bedrock Generative AI  
→ AWS Lambda APIs  
→ Streamlit AI Copilot Interface

---

# AWS Services Used

| Layer | Service | Purpose |
|------|------|------|
| Data Ingestion | AWS Lambda | Automated ingestion pipelines |
| Data Storage | Amazon S3 | Centralized data lake |
| Data Processing | AWS Glue (ETL Jobs, Crawlers) | Data transformation and catalog |
| Query Layer | Amazon Athena | Serverless SQL queries |
| Machine Learning | Amazon SageMaker | Model training and prediction |
| Generative AI | Amazon Bedrock | Natural language AI Copilot |
| API Layer | AWS Lambda | Business logic and inference orchestration |
| User Interface | Streamlit | Interactive analytics dashboard |

---

# Data Architecture

The project uses an **S3-based data lake architecture**.

```
s3://propelnoi-datalake/

raw/
    portfolio-data
    market-data
    economic-data

processed/
    curated-datasets

modeling/
    training-data
    inference-data

outputs/
    output_noi_forecast_ml
    output_market_rent_predictions
    output_maintenance_risk_predictions
```

---

# Machine Learning Models

| Model | Purpose |
|------|------|
| DeepAR Time Series Model | Forecast NOI |
| XGBoost Regression | Predict market rent |
| Random Forest Classifier | Detect maintenance risk |

All models are trained and deployed using **Amazon SageMaker**.

---

# AI Copilot

The AI Copilot is powered by **Amazon Bedrock**.

User prompts are processed through Lambda APIs that retrieve structured data from Athena and provide context to the LLM.

Example queries:

- Which properties are under market rent?
- What is the forecasted NOI next quarter?
- Which assets have the highest maintenance risk?

The Copilot generates natural language explanations for portfolio insights.

---

# Streamlit Application

The user interface is built using **Streamlit**.

Features include:

- Portfolio performance dashboard
- NOI forecast visualization
- Market rent gap analysis
- Maintenance risk insights
- AI Copilot chat interface

---

# Working Prototype

[Insert Streamlit URL here](http://13.201.122.89:8501/)

---

# Demo Video

PropelNOI: AI-Driven Margin Optimization for Real Estate Explanation:
https://www.loom.com/share/21ef883d9f444b998e52d17bce0e803b


PropelNOI: AI-Driven Margin Optimization for Real Estate Demonstration:
https://www.loom.com/share/08a4e1eb784d4852b773b31e92ebc9dd

---

# Limitations & Assumptions
- Portfolio & market data are synthetic (no real PII).
- Forecasting models are trained on limited historical datasets.
- Rent & maintenance models use simplified similarity and heuristic logic.
- Batch processing only (no real-time ingestion).
- LLM responses may be non-deterministic.
- System provides advisory insights, not automated financial decisions.

---

# Future Enhancements

- Real listing API integration
- Real-time streaming (Kinesis)
- Enterprise-grade governance & compliance controls
- Multi-portfolio benchmarking
- Integration with real property management systems
- Real-time data ingestion pipelines
- Larger historical datasets for model training
---

## Author
Created by [@lattalavijaysekhar] - feel free to contact me!
AWS AI Hackathon Submission
