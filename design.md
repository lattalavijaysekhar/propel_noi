# PropelNOI - Technical Design & Architecture
**Author:** Vijay Sekhar Lattala  
**Date:** February 5, 2026  
**Version:** 1.0  

## 1. System Overview

PropelNOI is a serverless, event-driven architecture built on AWS that combines real-time data ingestion, machine learning forecasting, and generative AI reasoning to provide margin-aware insights for real estate portfolios.

### Architecture Principles
- **Serverless-first**: Minimize operational overhead using AWS managed services
- **Event-driven**: Decouple components using event streams for scalability
- **Data-centric**: Design around data flow from ingestion to insights
- **AI-native**: Integrate ML and GenAI as core system capabilities

---

## 2. High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Data Pipeline  │    │  ML & AI Layer  │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Synthetic     │───▶│ • S3 Data Lake   │───▶│ • SageMaker     │
│   Portfolio     │    │ • Glue ETL       │    │ • Bedrock       │
│ • Market APIs   │    │ • Athena Query   │    │ • Lambda ML     │
│ • Economic Data │    │ • EventBridge    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  User Interface │◀───│  API Gateway     │◀───│  Core Services  │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • QuickSight    │    │ • REST APIs      │    │ • NOI Predictor │
│ • Web Dashboard │    │ • WebSocket      │    │ • Rent Analyzer │
│ • Copilot Chat  │    │ • Authentication │    │ • Maintenance   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 3. Data Architecture

### 3.1 Data Lake Structure (S3)

```
propel-noi-data-lake/
├── raw/                    # Landing zone for all incoming data
│   ├── portfolio/          # Synthetic property and financial data
│   ├── market/             # Public rental listings and comparables
│   └── economic/           # Inflation, interest rates, indicators
├── processed/              # Cleaned and transformed data
│   ├── properties/         # Normalized property details
│   ├── financials/         # Standardized rent rolls and expenses
│   └── market-signals/     # Processed market indicators
└── analytics/              # Analysis-ready datasets
    ├── noi-forecasts/      # ML model outputs
    ├── rent-gaps/          # Market comparison results
    └── maintenance-risks/  # Predictive maintenance scores
```

### 3.2 Data Flow Pipeline

1. **Ingestion Layer**
   - Lambda functions for API data collection
   - S3 event triggers for file uploads
   - EventBridge for scheduled data pulls

2. **Processing Layer**
   - AWS Glue for ETL transformations
   - Glue Data Catalog for schema management
   - Athena for ad-hoc querying

3. **Analytics Layer**
   - SageMaker for ML model training/inference
   - Lambda for real-time calculations
   - Bedrock for AI reasoning

---

## 4. Core Service Components

### 4.1 NOI Predictor Service

**Purpose**: Generate 12-month NOI forecasts using time-series analysis

**Architecture**:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Historical  │───▶│ SageMaker    │───▶│ Forecast API    │
│ NOI Data    │    │ Time Series  │    │ (Lambda)        │
│ (S3/Athena) │    │ Model        │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │ Model Store  │    │ Results Cache   │
                   │ (S3)         │    │ (DynamoDB)      │
                   └──────────────┘    └─────────────────┘
```

**Implementation**:
- **Model**: SageMaker DeepAR for time-series forecasting
- **Features**: Rental income, operating expenses, market indicators
- **Training**: Monthly retraining with new data
- **Inference**: Real-time via Lambda, batch via SageMaker Processing

### 4.2 Market-Rent Harmonizer Service

**Purpose**: Compare portfolio rents with market rates to identify gaps

**Architecture**:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Portfolio   │    │ Comparison   │    │ Gap Analysis    │
│ Rent Data   │───▶│ Engine       │───▶│ API             │
│             │    │ (Lambda)     │    │ (Lambda)        │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   ▲                      │
       ▼                   │                      ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Market      │    │ Matching     │    │ Recommendations │
│ Rent Data   │    │ Algorithm    │    │ (DynamoDB)      │
│             │    │              │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
```

**Implementation**:
- **Matching Logic**: Property type, location, size, amenities
- **Gap Calculation**: Percentage difference and dollar impact
- **Refresh Rate**: Daily market data updates
- **Storage**: DynamoDB for fast lookups

### 4.3 Predictive Maintenance Shield Service

**Purpose**: Identify high-risk maintenance issues before they occur

**Architecture**:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Maintenance │───▶│ Risk Scoring │───▶│ Alert System    │
│ History     │    │ Model        │    │ (Lambda + SNS)  │
│             │    │ (SageMaker)  │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   │                      │
       ▼                   ▼                      ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Property    │    │ Cost         │    │ Risk Dashboard  │
│ Age/Condition│    │ Estimates    │    │ (QuickSight)    │
│             │    │              │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
```

**Implementation**:
- **Risk Model**: Random Forest for maintenance probability
- **Features**: Property age, previous repairs, system types
- **Scoring**: 0-100 risk score with cost estimates
- **Alerts**: SNS notifications for high-risk items

### 4.4 Bedrock Insights (What-If Copilot)

**Purpose**: Natural language interface for financial modeling and analysis

**Architecture**:
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ User Query  │───▶│ Intent       │───▶│ Data Retrieval  │
│ (Natural    │    │ Recognition  │    │ (Athena/Lambda) │
│ Language)   │    │ (Bedrock)    │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │ Financial    │    │ Response        │
                   │ Calculations │    │ Generation      │
                   │ (Lambda)     │    │ (Bedrock)       │
                   └──────────────┘    └─────────────────┘
```

**Implementation**:
- **LLM**: Claude 3 via Bedrock for reasoning
- **Function Calling**: Lambda functions for calculations
- **Context**: RAG with portfolio and market data
- **Memory**: DynamoDB for conversation history

---

## 5. API Design

The system exposes a minimal REST-based API through Amazon API Gateway.

### Core Endpoints

GET  /properties/{id}/noi/forecast  
GET  /properties/{id}/rent/analysis  
GET  /properties/{id}/maintenance/risks  
POST /copilot/query  

All endpoints are backed by AWS Lambda functions and return JSON responses.

Authentication is handled via Amazon Cognito (JWT-based).

---

## 6. Machine Learning Models

### 6.1 NOI Forecasting Model

**Algorithm**: Amazon SageMaker DeepAR
**Features**:
- Historical NOI (24+ months)
- Rental income trends
- Operating expense patterns
- Market indicators (inflation, interest rates)
- Seasonal factors

**Training**:
- Frequency: Monthly
- Data: 24+ months historical
- Validation: Time-series cross-validation
- Metrics: MAPE, RMSE, directional accuracy

### 6.2 Rent Gap Detection Model

**Algorithm**: Similarity-based matching + regression
**Features**:
- Property characteristics (size, type, amenities)
- Location factors (neighborhood, transit)
- Market conditions
- Comparable properties

**Implementation**:
- Similarity scoring using cosine distance
- Price prediction using linear regression
- Gap calculation and ranking

### 6.3 Maintenance Risk Model

**Algorithm**: Random Forest Classifier
**Features**:
- Property age and condition
- Historical maintenance costs
- System types (HVAC, plumbing, electrical)
- Usage patterns
- Environmental factors

**Output**:
- Risk probability (0-1)
- Cost estimate with confidence interval
- Recommended action timeline

---

## 7. Security Considerations

- Data encrypted at rest (S3 default encryption)
- TLS for API communication
- IAM roles with least privilege
- Synthetic data only (no PII)

---

## 8. Monitoring

- Amazon CloudWatch for logs and metrics
- Basic error alerts via SNS
- Manual validation of ML outputs during demo phase

---

## 9. Deployment Strategy

The system will be deployed using AWS console and basic CloudFormation templates.

- Single AWS region deployment
- Serverless architecture (Lambda + S3 + API Gateway)
- Manual deployment for hackathon submission

---

## 10. Estimated Cost (Hackathon Scale)

PropelNOI follows a **serverless, pay-per-use AWS architecture** to minimize infrastructure overhead during the hackathon phase.

The system is designed for:
- Synthetic/public datasets only
- Batch forecasting (no always-on endpoints)
- Light copilot usage
- No heavy production traffic

### 10.1 Estimated Cost (15-Day Hackathon Usage)

| Service | Estimated 15-Day Cost |
|----------|-----------------------|
| Amazon S3 | $1 – $2 |
| AWS Glue | $3 – $5 |
| Amazon Athena | $2 – $4 |
| Amazon SageMaker (Batch Training) | $10 – $20 |
| Amazon Bedrock (Claude) | $4 – $12 |
| AWS Lambda & EventBridge | $0 – $3 |
| Amazon CloudWatch | $1 – $3 |
| Amazon QuickSight (Optional) | ~$12 |

### 10.2 Total Estimated Cost

- **Without QuickSight:** ~$25 – $50  
- **With QuickSight:** ~$40 – $65  

> Costs vary by region and usage volume. This estimate reflects hackathon-scale deployment only.

---

## 11. Hackathon Implementation Plan (15 Days)

### Phase 1 – Data & Infrastructure (Days 1–5)

- Set up S3 data lake (raw + processed zones)
- Build Glue ETL pipeline
- Configure Athena queries
- Create synthetic portfolio dataset
- Implement Lambda ingestion logic

### Phase 2 – ML Model Development (Days 6–9)

- Train NOI forecasting model using SageMaker (DeepAR)
- Implement rent gap detection logic
- Build maintenance risk scoring model
- Validate outputs using synthetic scenarios

### Phase 3 – AI Copilot Integration (Days 10–12)

- Integrate Amazon Bedrock (Claude)
- Implement natural language “What-if” analysis
- Connect Lambda financial calculation functions
- Generate prescriptive recommendations

### Phase 4 – Dashboard & Demo (Days 13–15)

- Create QuickSight dashboard
- Connect ML outputs to visualization layer
- Prepare demo scenarios
- Final testing and deployment

---

## 12. Design Decisions & Rationale

### 12.1 Why Serverless Architecture?

- No infrastructure management required
- Pay-per-use pricing model
- Rapid development cycle
- Auto-scaling for demo workloads

### 12.2 Why Amazon Bedrock?

- No model hosting overhead
- Pay-per-token pricing
- Strong reasoning capability (Claude)
- Faster integration than self-hosted LLMs

### 12.3 Why Amazon SageMaker?

- Built-in time-series forecasting algorithms
- Spot training reduces cost
- Managed ML infrastructure
- Quick batch inference deployment

### 12.4 Why S3 + Athena?

- Cost-effective data lake architecture
- SQL-based analytics
- No database administration
- Easily scalable for production expansion

The overall architecture prioritizes:
- Simplicity
- Cost efficiency
- Rapid prototyping
- Production scalability

---

## 13. Success Metrics

### 13.1 Technical Metrics

- Generate 12-month NOI forecast
- Identify under-rented units from synthetic portfolio
- Produce maintenance risk score
- Enable natural language financial modeling
- API response time < 1 second (demo scale)

### 13.2 Business Impact Metrics

- Simulated 2–5% NOI optimization opportunity
- Demonstrated margin leakage detection
- Generated prescriptive financial recommendations
- Reduced insight time from quarterly reviews to real-time analysis

---

## 14. Limitations & Assumptions

### 14.1 Assumptions

For the hackathon implementation, the following assumptions are made:

- Portfolio data is synthetic and does not contain real tenant or PII information.
- Public market data (e.g., rental listings, inflation metrics) is sampled or simulated.
- Forecasting models are trained on limited historical synthetic datasets.
- System usage during demo is light and not production-scale.
- Users are assumed to be investment analysts or property managers with basic financial literacy.
- Internet connectivity and AWS service availability are stable during demo execution.

---

### 14.2 Technical Limitations

- NOI forecasts are based on limited synthetic historical data and may not reflect real-world volatility.
- Rent comparison logic may rely on simplified similarity scoring rather than full production-grade scraping pipelines.
- Maintenance risk model uses heuristic or small training datasets rather than extensive IoT or real asset data.
- Bedrock copilot responses depend on prompt engineering and may occasionally produce non-deterministic outputs.
- Real-time streaming ingestion is not implemented (batch-oriented processing only).
- Security implementation is minimal (IAM roles, encryption by default), without enterprise-grade compliance controls.

---

### 14.3 Cost & Scale Limitations

- Cost estimates are based on hackathon-scale workloads only.
- Production-scale usage (thousands of properties, high concurrent users) would require:
  - Additional optimization
  - Caching strategies
  - API rate limiting
  - Enhanced monitoring
- Spot training jobs may experience interruptions (mitigated via checkpointing).

---

### 14.4 Business Limitations

- The system provides prescriptive insights but does not automate financial decisions.
- ROI projections are simulated based on synthetic portfolio performance.
- Zoning change impacts are modeled conceptually, not connected to live municipal data feeds.
- Market-rent harmonization assumes comparable property data is sufficiently available.

---

### 14.5 Future Enhancements

- Integration with real listing APIs
- Real-time streaming data ingestion (Kinesis)
- Advanced anomaly detection for sudden NOI shifts
- Multi-portfolio benchmarking
- Enterprise-grade governance and audit tracking

---

This comprehensive design ensures PropelNOI delivers measurable value while maintaining cost-effectiveness and technical excellence.






