import json
import time
import os
import boto3

# AWS clients
athena = boto3.client("athena")

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("BEDROCK_REGION", "ap-south-1")
)

DATABASE = os.environ.get("DATABASE", "propelnoi_db")

ATHENA_OUTPUT = os.environ.get(
    "ATHENA_OUTPUT",
    "s3://propelnoi-vijay-datalake/outputs/athenaresults/"
)

MODEL_ID = os.environ.get(
    "MODEL_ID",
    "apac.anthropic.claude-sonnet-4-20250514-v1:0"
)


# -----------------------------------------------------
# API RESPONSE
# -----------------------------------------------------
def api_response(code, payload):

    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(payload, default=str)
    }


# -----------------------------------------------------
# RUN ATHENA QUERY
# -----------------------------------------------------
def run_athena_query(query):

    start = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
    )

    qid = start["QueryExecutionId"]

    while True:

        status = athena.get_query_execution(QueryExecutionId=qid)

        state = status["QueryExecution"]["Status"]["State"]

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

        time.sleep(2)

    if state != "SUCCEEDED":

        reason = status["QueryExecution"]["Status"].get(
            "StateChangeReason",
            "Unknown Athena failure"
        )

        raise Exception(f"Athena query failed: {reason}")

    paginator = athena.get_paginator("get_query_results")

    pages = paginator.paginate(QueryExecutionId=qid)

    headers = None
    rows_out = []

    for page in pages:

        rows = page["ResultSet"]["Rows"]

        if not rows:
            continue

        if headers is None:

            headers = [c.get("VarCharValue", "") for c in rows[0]["Data"]]

            rows = rows[1:]

        for row in rows:

            vals = [c.get("VarCharValue", None) for c in row["Data"]]

            if len(vals) < len(headers):
                vals.extend([None] * (len(headers) - len(vals)))

            rows_out.append(dict(zip(headers, vals)))

    return rows_out


# -----------------------------------------------------
# BEDROCK CALL
# -----------------------------------------------------
def call_bedrock(prompt):

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 700,
        "temperature": 0.1,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    payload = json.loads(response["body"].read())

    return payload["content"][0]["text"]


# -----------------------------------------------------
# GENERATE SQL USING BEDROCK
# -----------------------------------------------------
def generate_sql(question):

    prompt = f"""
You are a data analytics assistant.

Convert the user's question into an Athena SQL query.

Database: propelnoi_db

Tables available:

1. output_market_rent_predictions
columns:
property_id
month
city
current_portfolio_rent
predicted_market_rent
recommended_rent
rent_gap
rent_gap_pct
rent_status
confidence_score
annual_rent_opportunity

2. output_noi_forecast_ml
columns:
property_id
forecast_month
predicted_noi
lower_bound
upper_bound

Rules:

- Always limit results to 20 rows
- When querying rent gaps use latest month per property
- Use ORDER BY ABS(rent_gap) DESC for opportunities
- Do not return explanation
- Return ONLY SQL

User question:
{question}
"""

    sql = call_bedrock(prompt)

    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql


# -----------------------------------------------------
# GENERATE BUSINESS INSIGHT
# -----------------------------------------------------
def generate_insight(question, data):

    prompt = f"""
You are a real estate investment analytics copilot.

User question:
{question}

Query results:
{json.dumps(data, indent=2)}

Instructions:

Explain insights in business language.

Mention:
• rent gaps
• opportunity
• percentage gaps
• recommended actions

Do NOT hallucinate numbers.
"""

    return call_bedrock(prompt)


# -----------------------------------------------------
# LAMBDA HANDLER
# -----------------------------------------------------
def lambda_handler(event, context):

    try:

        body = event.get("body")

        if isinstance(body, str):
            body = json.loads(body)

        if body is None:
            body = event

        question = body.get("question")

        if not question:

            return api_response(
                400,
                {"error": "question required"}
            )

        # STEP 1 Generate SQL
        sql = generate_sql(question)

        print("Generated SQL:", sql)

        # STEP 2 Run Athena
        data = run_athena_query(sql)

        if not data:

            return api_response(
                200,
                {
                    "question": question,
                    "answer": "No matching data found",
                    "sql": sql,
                    "data": []
                }
            )

        # STEP 3 Generate insight
        insight = generate_insight(question, data)

        return api_response(
            200,
            {
                "question": question,
                "sql": sql,
                "answer": insight,
                "data": data
            }
        )

    except Exception as e:

        return api_response(
            500,
            {"error": str(e)}
        )