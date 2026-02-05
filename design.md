# PropelNOI — Technical Design & Architecture

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

### 5.1 REST API Endpoints

**Base URL**: `https://api.propelnoi.com/v1`

```
# NOI Forecasting
GET    /properties/{id}/noi/forecast?months=12
POST   /properties/batch/noi/forecast
GET    /portfolio/noi/forecast

# Market Analysis
GET    /properties/{id}/rent/analysis
GET    /properties/{id}/rent/recommendations
POST   /properties/batch/rent/analysis

# Maintenance Predictions
GET    /properties/{id}/maintenance/risks
GET    /properties/{id}/maintenance/schedule
POST   /properties/batch/maintenance/risks

# Copilot Interface
POST   /copilot/query
GET    /copilot/history/{session_id}
POST   /copilot/scenario
```

### 5.2 WebSocket API (Real-time Updates)

```
# Connection Management
wss://ws.propelnoi.com/v1/connect

# Message Types
{
  "type": "noi_forecast_update",
  "property_id": "prop_123",
  "forecast": {...}
}

{
  "type": "market_alert",
  "alert_type": "rent_gap_detected",
  "properties": [...]
}

{
  "type": "maintenance_alert",
  "property_id": "prop_123",
  "risk_score": 85,
  "estimated_cost": 5000
}
```

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

## 7. Security & Compliance

### 7.1 Data Security

- **Encryption**: AES-256 for data at rest (S3, DynamoDB)
- **Transit**: TLS 1.3 for all API communications
- **Access Control**: IAM roles with least privilege
- **API Security**: API Gateway with rate limiting and authentication

### 7.2 Authentication & Authorization

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ User Login  │───▶│ Cognito      │───▶│ JWT Token       │
│             │    │ User Pool    │    │ Validation      │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │ Role-Based   │    │ API Gateway     │
                   │ Permissions  │    │ Authorizer      │
                   └──────────────┘    └─────────────────┘
```

### 7.3 Data Privacy

- **Synthetic Data**: No real tenant or lease information
- **Data Masking**: PII removal from all datasets
- **Audit Logging**: CloudTrail for all data access
- **Retention**: Automated data lifecycle policies

---

## 8. Monitoring & Observability

### 8.1 Application Monitoring

- **Metrics**: CloudWatch for system metrics
- **Logging**: Structured logging with correlation IDs
- **Tracing**: X-Ray for distributed tracing
- **Alerting**: SNS for critical system alerts

### 8.2 ML Model Monitoring

- **Model Drift**: SageMaker Model Monitor
- **Performance**: Accuracy tracking over time
- **Data Quality**: Input validation and anomaly detection
- **Retraining**: Automated triggers based on performance degradation

### 8.3 Business Metrics

- **Forecast Accuracy**: MAPE tracking by property type
- **User Engagement**: API usage and copilot interactions
- **Value Generation**: Rent gap identification success rate
- **System Performance**: Response times and availability

---

## 9. Deployment Strategy

### 9.1 Infrastructure as Code

- **AWS CDK**: TypeScript for infrastructure definition
- **Environment Management**: Dev, staging, production
- **Configuration**: Parameter Store for environment-specific settings
- **Secrets**: Secrets Manager for API keys and credentials

### 9.2 CI/CD Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Code Commit │───▶│ CodeBuild    │───▶│ CodePipeline    │
│ (GitHub)    │    │ (Test/Build) │    │ (Deploy)        │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │ Artifact     │    │ CloudFormation  │
                   │ Store (S3)   │    │ Stacks          │
                   └──────────────┘    └─────────────────┘
```

### 9.3 Rollback Strategy

- **Blue/Green Deployment**: Lambda aliases for safe deployments
- **Database Migrations**: Backward-compatible schema changes
- **Model Versioning**: SageMaker model registry for rollbacks
- **Feature Flags**: Runtime configuration for feature toggles

---

## 10. Cost Optimization & Estimated Costs

### 10.1 Cost-Effective Architecture Decisions

**Serverless-First Approach**
- **Lambda**: Pay-per-execution, no idle costs
- **API Gateway**: Pay-per-request pricing
- **DynamoDB On-Demand**: Pay for actual usage
- **S3**: Storage-only costs, no compute overhead

**Smart Resource Selection**
- **SageMaker Spot Instances**: Up to 90% savings on training
- **Athena**: Query-based pricing, no infrastructure costs
- **Bedrock**: Pay-per-token, no model hosting fees
- **EventBridge**: Minimal costs for event routing

### 10.2 Detailed Cost Optimization Strategies

#### Compute Optimization
```
Lambda Functions:
├── Memory: 512MB (optimal for most functions)
├── Timeout: 30s max (prevent runaway costs)
├── Provisioned Concurrency: Only for critical APIs
└── ARM Graviton2: 20% cost savings where supported

SageMaker:
├── Training: Spot instances (up to 90% savings)
├── Inference: Serverless endpoints for low traffic
├── Processing: Spot instances for batch jobs
└── Model Store: S3 instead of model registry
```

#### Storage Optimization
```
S3 Storage Classes:
├── Standard: Hot data (current month)
├── Standard-IA: Warm data (3-12 months)
├── Glacier Flexible: Cold data (1+ years)
└── Intelligent Tiering: Automated optimization

Data Formats:
├── Parquet: 75% compression vs JSON
├── Partitioning: Reduce query costs by 80%
├── Columnar: Optimize for analytics workloads
└── Compression: GZIP/Snappy for additional savings
```

#### Query Optimization
```
Athena Best Practices:
├── Partition Pruning: Date/property-based partitions
├── Columnar Formats: Parquet over CSV/JSON
├── Query Caching: Reuse results for 24 hours
├── Result Compression: Reduce data transfer costs
└── Workgroup Limits: Prevent expensive queries
```

### 10.3 Estimated Implementation Costs

#### Hackathon Phase (4 Days)
**Development Environment Costs**

| Service | Usage | Monthly Cost | 4-Day Cost |
|---------|-------|--------------|------------|
| **Lambda** | 1M requests, 512MB, 5s avg | $8.35 | $1.11 |
| **API Gateway** | 100K requests | $0.35 | $0.05 |
| **S3** | 10GB storage, 1GB transfer | $0.25 | $0.03 |
| **DynamoDB** | 1M read/write units | $1.25 | $0.17 |
| **SageMaker Training** | 2 ml.m5.large spot (4 hours) | $1.60 | $1.60 |
| **Bedrock (Claude 3)** | 100K tokens | $0.80 | $0.80 |
| **Athena** | 10GB data scanned | $0.50 | $0.50 |
| **Glue** | 2 DPU-hours | $0.88 | $0.88 |
| **QuickSight** | 1 author license | $18.00 | $2.40 |
| **CloudWatch** | Basic monitoring | $3.00 | $0.40 |
| **EventBridge** | 10K events | $0.10 | $0.01 |
| **SNS** | 1K notifications | $0.50 | $0.07 |
| **Secrets Manager** | 2 secrets | $0.80 | $0.11 |
| **Parameter Store** | 10 parameters | $0.00 | $0.00 |
| **X-Ray** | 100K traces | $0.50 | $0.07 |
| **Data Transfer** | 5GB out | $0.45 | $0.45 |
| | | **Total: $37.33** | **$8.65** |

#### Production Environment (Monthly)
**Assuming 1,000 properties, 100 active users**

| Service | Usage | Optimized Cost | Notes |
|---------|-------|----------------|-------|
| **Lambda** | 10M requests, 512MB | $83.50 | Right-sized memory |
| **API Gateway** | 5M requests | $17.50 | Caching enabled |
| **S3** | 500GB (mixed tiers) | $8.50 | Intelligent tiering |
| **DynamoDB** | 50M read/write units | $62.50 | On-demand pricing |
| **SageMaker** | 20 hours training/month | $16.00 | Spot instances |
| **Bedrock** | 5M tokens/month | $40.00 | Claude 3 Haiku |
| **Athena** | 100GB scanned/month | $5.00 | Partitioned data |
| **Glue** | 40 DPU-hours/month | $17.60 | Scheduled jobs |
| **QuickSight** | 10 reader licenses | $50.00 | Reader tier |
| **CloudWatch** | Enhanced monitoring | $15.00 | Custom metrics |
| **EventBridge** | 1M events/month | $10.00 | Event routing |
| **Application Load Balancer** | 1 ALB | $16.20 | High availability |
| **NAT Gateway** | 100GB transfer | $45.00 | VPC connectivity |
| **Data Transfer** | 200GB out | $18.00 | CDN optimization |
| | | **Total: $405.30** | **Per month** |

#### Annual Production Cost Breakdown
```
Base Infrastructure: $405.30 × 12 = $4,863.60
Growth Buffer (50%): $2,431.80
Disaster Recovery: $1,215.90
Total Annual Cost: $8,511.30

Cost per Property: $8.51/year
Cost per User: $85.11/year
```

### 10.4 Cost Monitoring & Alerts

#### Budget Configuration
```json
{
  "budgets": [
    {
      "name": "PropelNOI-Development",
      "limit": "$50/month",
      "alerts": ["80%", "100%"]
    },
    {
      "name": "PropelNOI-Production",
      "limit": "$500/month",
      "alerts": ["70%", "85%", "100%"]
    }
  ]
}
```

#### Cost Allocation Tags
```
Environment: [dev, staging, prod]
Component: [api, ml, storage, compute]
Feature: [noi-predictor, rent-analyzer, maintenance, copilot]
Owner: [team-name]
Project: propel-noi
```

### 10.5 Cost Optimization Automation

#### Lambda Cost Optimizer
```python
# Auto-adjust Lambda memory based on usage
def optimize_lambda_memory():
    for function in lambda_functions:
        metrics = get_cloudwatch_metrics(function)
        if metrics.memory_utilization < 60:
            reduce_memory(function, 0.8)
        elif metrics.memory_utilization > 90:
            increase_memory(function, 1.2)
```

#### S3 Lifecycle Automation
```json
{
  "Rules": [
    {
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    }
  ]
}
```

### 10.6 Alternative Cost-Saving Approaches

#### Free Tier Maximization (First Year)
- **Lambda**: 1M free requests/month
- **DynamoDB**: 25GB free storage
- **S3**: 5GB free storage
- **CloudWatch**: 10 custom metrics free
- **API Gateway**: 1M free requests/month

**Estimated First-Year Savings: $1,200**

#### Reserved Instances (Year 2+)
- **RDS** (if needed): 40% savings with 1-year RI
- **EC2** (if scaling beyond serverless): 60% savings
- **ElastiCache** (for caching): 45% savings

#### Spot Instance Strategy
```
SageMaker Training Jobs:
├── Spot Price: $0.08/hour vs $0.80/hour on-demand
├── Savings: 90% on training costs
├── Fault Tolerance: Checkpointing every 5 minutes
└── Automatic Retry: On spot interruption
```

### 10.7 Cost vs. Performance Trade-offs

| Optimization | Cost Savings | Performance Impact | Recommendation |
|--------------|--------------|-------------------|----------------|
| Lambda ARM Graviton2 | 20% | Minimal | ✅ Implement |
| DynamoDB On-Demand | Variable | Better for spiky traffic | ✅ Use for hackathon |
| S3 Intelligent Tiering | 30-70% | Minimal | ✅ Implement |
| Athena Result Caching | 50% query costs | Faster repeated queries | ✅ Enable |
| SageMaker Spot Training | 90% | Potential interruptions | ✅ Use with checkpointing |
| QuickSight Reader Licenses | 75% vs Author | Limited editing | ✅ Use for end users |

### 10.8 ROI Analysis

#### Cost Justification
```
Monthly Operational Cost: $405.30
Cost per Property: $0.41/month
Cost per User: $4.05/month

Value Delivered:
├── NOI Optimization: 2-5% improvement
├── Maintenance Savings: 10-15% reduction
├── Rent Gap Recovery: 3-8% increase
└── Decision Speed: 75% faster insights

Break-even: 1% NOI improvement covers all costs
```

This cost-optimized design ensures PropelNOI remains economically viable while delivering maximum value through intelligent AWS service selection and automated cost management.

---

## 11. Hackathon Implementation Plan

### Phase 1: Core Infrastructure (Day 1)
- Set up S3 data lake structure
- Deploy basic Lambda functions
- Configure API Gateway
- Create synthetic data generators

### Phase 2: ML Models (Day 2)
- Implement NOI forecasting with SageMaker
- Build rent comparison logic
- Create maintenance risk scoring
- Set up model training pipelines

### Phase 3: AI Integration (Day 3)
- Integrate Bedrock for copilot functionality
- Implement natural language query processing
- Build response generation system
- Create conversation management

### Phase 4: Frontend & Demo (Day 4)
- Build simple web dashboard
- Create QuickSight visualizations
- Implement copilot chat interface
- Prepare demo scenarios and data

This design provides a solid foundation for building PropelNOI within the hackathon timeframe while maintaining scalability and best practices.