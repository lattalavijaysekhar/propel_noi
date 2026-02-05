# PropelNOI - Technical Design & Architecture
**Author:** Vijay  
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

#### Hackathon Phase (15 Days)
**Development Environment Costs**

| Service | Usage | Monthly Cost | 15-Day Cost |
|---------|-------|--------------|-------------|
| **Lambda** | 5M requests, 512MB, 5s avg | $41.75 | $20.88 |
| **API Gateway** | 500K requests | $1.75 | $0.88 |
| **S3** | 50GB storage, 10GB transfer | $1.50 | $0.75 |
| **DynamoDB** | 10M read/write units | $12.50 | $6.25 |
| **SageMaker Training** | 10 ml.m5.large spot (40 hours) | $16.00 | $16.00 |
| **Bedrock (Claude 3)** | 1M tokens | $8.00 | $8.00 |
| **Athena** | 100GB data scanned | $5.00 | $5.00 |
| **Glue** | 20 DPU-hours | $8.80 | $8.80 |
| **QuickSight** | 1 author license | $18.00 | $9.00 |
| **CloudWatch** | Enhanced monitoring | $10.00 | $5.00 |
| **EventBridge** | 100K events | $1.00 | $0.50 |
| **SNS** | 10K notifications | $5.00 | $2.50 |
| **Secrets Manager** | 5 secrets | $2.00 | $1.00 |
| **Parameter Store** | 50 parameters | $0.00 | $0.00 |
| **X-Ray** | 1M traces | $5.00 | $2.50 |
| **Data Transfer** | 25GB out | $2.25 | $2.25 |
| **VPC/NAT Gateway** | Development setup | $22.50 | $11.25 |
| | | **Total: $161.05** | **$100.56** |

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
| DynamoDB On-Demand | Variable | Better for spiky traffic | ✅ Ideal for production |
| S3 Intelligent Tiering | 30-70% | Minimal | ✅ Implement |
| Athena Result Caching | 50% query costs | Faster repeated queries | ✅ Enable |
| SageMaker Spot Training | 90% | Potential interruptions | ✅ Use with checkpointing |
| QuickSight Reader Licenses | 75% vs Author | Limited editing | ✅ Use for end users |

### 10.8 ROI Analysis

#### Cost Justification
```
Monthly Operational Cost: $405.30
Cost per Property: $0.41/month ($4.92/year)
Cost per User: $4.05/month ($48.60/year)

Typical Real Estate Portfolio Metrics:
├── Average Property NOI: $12,000/year
├── Portfolio Size: 1,000 properties
├── Total Portfolio NOI: $12,000,000/year
└── System Cost as % of NOI: 0.07%

Value Delivered:
├── NOI Optimization: 2-5% improvement ($240,000-$600,000/year)
├── Maintenance Savings: 10-15% reduction ($120,000-$180,000/year)
├── Rent Gap Recovery: 3-8% increase ($360,000-$960,000/year)
└── Decision Speed: 75% faster insights

Total Potential Value: $720,000 - $1,740,000/year
Annual System Cost: $4,863.60/year

Break-even Analysis:
├── Break-even NOI improvement: 0.04% (4 basis points)
├── Break-even per property: $4.86/year improvement
├── Monthly break-even per property: $0.41/month
└── ROI Range: 148x to 358x return on investment

Conservative Scenario (1% NOI improvement):
├── Annual benefit: $120,000
├── Annual cost: $4,863.60
└── ROI: 2,467% (25x return)
```

**Even a tiny 0.04% NOI improvement covers all costs!**

This makes PropelNOI extremely compelling - the system pays for itself with minimal performance gains, while typical results show 2-5% NOI improvements, delivering massive ROI.

This cost-optimized design ensures PropelNOI remains economically viable while delivering maximum value through intelligent AWS service selection and automated cost management.

---

## 11. Hackathon Implementation Plan
  
**Assumed Timeline: February 25 - March 11, 2026 (15 days)**

### Week 1: Foundation & Core Services (Feb 25 - Mar 3)

#### Days 1-2 (Feb 25-26): Infrastructure Setup
- Set up AWS account and IAM roles
- Create S3 data lake structure with proper partitioning
- Deploy basic Lambda functions for data ingestion
- Configure API Gateway with authentication
- Set up CloudWatch monitoring and logging
- Create synthetic data generators for portfolio and market data

#### Days 3-4 (Feb 27-28): Data Pipeline
- Implement AWS Glue ETL jobs for data transformation
- Set up Athena for data querying with optimized partitions
- Create DynamoDB tables with proper indexing
- Build data validation and quality checks
- Test end-to-end data flow from ingestion to storage

#### Days 5-7 (Mar 1-3): ML Model Development
- Implement NOI forecasting using SageMaker DeepAR
- Build rent comparison algorithm with similarity matching
- Create maintenance risk scoring model
- Set up model training pipelines with spot instances
- Validate model accuracy with synthetic data

### Week 2: AI Integration & Frontend (Mar 4 - Mar 10)

#### Days 8-9 (Mar 4-5): Bedrock Integration
- Integrate Amazon Bedrock with Claude 3 Haiku
- Implement natural language query processing
- Build function calling for financial calculations
- Create conversation management system
- Test copilot responses with sample queries

#### Days 10-11 (Mar 6-7): API Development
- Complete REST API endpoints for all features
- Implement WebSocket for real-time updates
- Add proper error handling and validation
- Create API documentation with examples
- Perform load testing and optimization

#### Days 12-13 (Mar 8-9): Frontend & Visualization
- Build responsive web dashboard using React/Vue
- Create QuickSight dashboards for executives
- Implement copilot chat interface
- Add data visualization components
- Ensure mobile-responsive design

#### Day 14 (Mar 10): Integration, Testing, and Deployment
- End-to-end system testing
- Performance optimization
- Security review and fixes
- Demo scenario preparation
- Documentation finalization
- Deploy to production environment

### Final Day: Submission (Mar 11)

### Risk Mitigation Strategies

#### Technical Risks
- **Model Training Delays**: Use pre-trained models as fallback
- **API Integration Issues**: Build mock services for testing
- **AWS Service Limits**: Request limit increases early
- **Data Quality Problems**: Implement robust validation

#### Timeline Risks
- **Scope Creep**: Stick to MVP features only
- **Integration Complexity**: Test components independently first
- **Performance Issues**: Use caching and optimization from day 1
- **Last-minute Bugs**: Code freeze 24 hours before submission

### Success Milestones

#### Week 1 Checkpoints
- [ ] Data pipeline fully functional (Day 4)
- [ ] At least one ML model trained and deployed (Day 6)
- [ ] Basic API endpoints working (Day 7)

#### Week 2 Checkpoints
- [ ] Bedrock integration complete (Day 9)
- [ ] Frontend dashboard functional (Day 12)
- [ ] End-to-end demo ready (Day 14)

This 15-day implementation plan provides sufficient time for a robust prototype while maintaining focus on core value propositions and demo readiness.

This design provides a solid foundation for building PropelNOI within the hackathon timeframe while maintaining scalability and best practices.

---

## 12. Design Decisions & Rationale

### Why Serverless Architecture?
I chose a serverless-first approach because:
- **Cost Efficiency**: Pay only for actual usage, critical for hackathon budget
- **Rapid Development**: Focus on business logic, not infrastructure management
- **Auto Scaling**: Handle variable loads without manual intervention
- **Reduced Complexity**: Minimal operational overhead for a 4-day timeline

### Why These Specific AWS Services?
My service selection rationale:

**Amazon Bedrock over Self-Hosted LLMs**
- No model management overhead
- Pay-per-token pricing fits hackathon usage
- Claude 3 provides excellent reasoning capabilities
- Faster integration than custom deployments

**SageMaker over Custom ML Infrastructure**
- Built-in algorithms (DeepAR) for time-series forecasting
- Spot instance support for 90% cost savings
- Managed model endpoints for easy deployment
- Integrated with other AWS services

**DynamoDB over RDS**
- Serverless scaling matches application architecture
- Sub-millisecond latency for real-time queries
- On-demand pricing aligns with usage patterns
- No database administration required

### Data Architecture Philosophy
I designed the data lake with three tiers:
1. **Raw**: Preserve original data integrity
2. **Processed**: Standardized for analytics
3. **Analytics**: Optimized for ML and reporting

This approach ensures data lineage while optimizing for different access patterns and cost structures.

---

## 13. Success Metrics & KPIs

### Technical Performance
- **API Response Time**: < 500ms for 95th percentile
- **ML Model Accuracy**: > 85% for 3-month NOI forecasts
- **System Availability**: > 99.5% uptime
- **Cost Efficiency**: < $0.50 per property per month

### Business Value
- **NOI Improvement**: 2-5% average increase
- **Maintenance Cost Reduction**: 10-15% savings
- **Rent Gap Recovery**: 3-8% revenue increase
- **Decision Speed**: 75% faster insights delivery

### User Experience
- **Copilot Response Quality**: > 90% user satisfaction
- **Dashboard Load Time**: < 3 seconds
- **Query Success Rate**: > 95% for natural language queries
- **User Adoption**: > 80% monthly active usage

This comprehensive design ensures PropelNOI delivers measurable value while maintaining cost-effectiveness and technical excellence.


