# PropelNOI — Requirements.md (Hackathon)

## 1. Problem Statement

Real estate investors and property managers suffer from **"Data Blindness."**  

While they maintain internal rent rolls and expense data, they lack **real-time visibility into how external market shifts**—such as inflation, competitor pricing, and zoning changes—impact **Net Operating Income (NOI)**.

As a result:
- Decisions are made quarterly
- Margin erosion happens daily
- Risks are discovered only after NOI declines

**Core problem:**  
> *"NOI erosion is detected too late to act."*

---

## 2. Unique Selling Proposition (USP)

**PropelNOI is a Margin-Aware AI Copilot for Real Estate.**

Unlike traditional dashboards that show historical KPIs, PropelNOI:
- Cross-references **public market signals** with **synthetic portfolio data**
- Uses **generative AI reasoning** to explain *why* NOI is changing
- Provides **prescriptive actions**, not just descriptive analytics

**USP in one line:**  
> *PropelNOI explains what is hurting NOI, why it's happening, and what action can improve it.*

---

## 3. Goals / Core Features

PropelNOI aims to **protect and grow NOI proactively** by answering four key questions:

1. What will my NOI look like over the next 12 months?
2. Which units are under-rented relative to the market?
3. Where are future maintenance costs likely to spike?
4. What happens to NOI if market or cost assumptions change?

These goals are delivered through four core features:
- NOI Predictor  
- Market-Rent Harmonizer  
- Predictive Maintenance Shield  
- Bedrock Insights (What-If Copilot)

---

## 4. Data to Be Used (Public & Synthetic Only)

### Synthetic Data
- Property and unit details
- Rent rolls
- Operating expenses
- Maintenance history
- Asset age and condition

### Publicly Available Data
- Inflation rates
- Interest rates
- Public rental listings (or mocked equivalents)
- Public zoning or policy indicators (simulated)

**Data Constraints**
- No real tenant or lease data
- No proprietary or paid datasets
- All synthetic data is reproducible

---

## 5. AWS Services Used (Limited for Hackathon)

Only the minimum AWS services required are used:

| Purpose | AWS Service |
|------|------------|
| Data storage | Amazon S3 |
| Data preparation | AWS Glue |
| Query & analysis | Amazon Athena |
| Forecasting | Amazon SageMaker |
| GenAI reasoning | Amazon Bedrock |
| Backend logic | AWS Lambda |
| Visualization | Amazon QuickSight or simple web UI |

---

## 6. Core Features — What We Do & Success Criteria

### 6.1 NOI Predictor

**What it does**
- Forecasts NOI for the next 12 months using time-series analysis
- Incorporates rental income, expenses, and inflation trends
- Produces a forward-looking NOI projection

**Success Criteria**
- 12-month NOI forecast is generated
- Forecast drivers (income vs expenses) are visible
- Results are accessible via dashboard and copilot

---

### 6.2 Market-Rent Harmonizer

**What it does**
- Compares in-place rent with public market rent
- Identifies under-rented units
- Estimates unrealized NOI due to rent gaps

**Success Criteria**
- Under-rented units are flagged
- Rent gap percentage is calculated
- NOI impact is estimated and explained

---

### 6.3 Predictive Maintenance Shield

**What it does**
- Analyzes historical maintenance cost patterns
- Flags units with rising repair cost trends
- Estimates future expense impact on NOI

**Success Criteria**
- High-risk units are identified
- Estimated cost impact is shown
- Risk is clearly linked to NOI erosion

---

### 6.4 Bedrock Insights (What-If Copilot)

**What it does**
- Enables natural-language financial questions such as:
  - "Why is NOI declining?"
  - "What if rent increases by 5%?"
  - "What if operating costs rise due to inflation?"
- Uses Amazon Bedrock to reason over forecasts and comparisons

**Success Criteria**
- Copilot answers at least three financial "what-if" questions
- Responses include assumptions and explanations
- Outputs are grounded in portfolio and market data

---

## 7. Trade-offs & Limitations

- Portfolio and expense data are synthetic and illustrative
- Market rent data may be simulated or delayed
- Forecasting models are simplified for hackathon scope
- Maintenance risk detection is rule-based
- The system provides **decision support**, not automated execution

---

## Hackathon Fit

PropelNOI demonstrates:
- Strong business relevance (NOI protection)
- Data-driven decision making
- Practical commercial value
- Responsible and explainable AI
- Focused use of AWS services