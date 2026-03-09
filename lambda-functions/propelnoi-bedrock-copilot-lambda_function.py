import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import boto3

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
DEFAULT_MAX_ROWS = int(os.environ.get("DEFAULT_MAX_ROWS", "10"))
ATHENA_POLL_SECONDS = float(os.environ.get("ATHENA_POLL_SECONDS", "1.0"))


def api_response(code: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(payload, default=str),
    }


def parse_event_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body") if isinstance(event, dict) else None
    if isinstance(body, str):
        body = json.loads(body)
    if isinstance(body, dict):
        return body
    return event if isinstance(event, dict) else {}


def sanitize_text(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9 _\\-]", "", value or "")
    return safe.replace("'", "''").strip()


def to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def call_bedrock(prompt: str, max_tokens: int = 500) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    payload = json.loads(response["body"].read())
    return payload["content"][0]["text"].strip()


def run_athena_query(query: str) -> List[Dict[str, Any]]:
    start = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
    )
    qid = start["QueryExecutionId"]

    while True:
        execution = athena.get_query_execution(QueryExecutionId=qid)
        status = execution["QueryExecution"]["Status"]
        state = status["State"]
        if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            break
        time.sleep(ATHENA_POLL_SECONDS)

    if state != "SUCCEEDED":
        reason = status.get("StateChangeReason", "Unknown Athena failure")
        raise Exception(f"Athena query failed: {reason}")

    paginator = athena.get_paginator("get_query_results")
    pages = paginator.paginate(QueryExecutionId=qid)

    headers = None
    output = []

    for page in pages:
        rows = page["ResultSet"]["Rows"]
        if not rows:
            continue

        if headers is None:
            headers = [cell.get("VarCharValue", "") for cell in rows[0]["Data"]]
            rows = rows[1:]

        for row in rows:
            values = [cell.get("VarCharValue", None) for cell in row["Data"]]
            if len(values) < len(headers):
                values.extend([None] * (len(headers) - len(values)))
            output.append(dict(zip(headers, values)))

    return output


def extract_city(question: str) -> Optional[str]:
    patterns = [
        r"\bin\s+([A-Za-z][A-Za-z \-]+)\??$",
        r"\bfor\s+([A-Za-z][A-Za-z \-]+)\??$",
    ]
    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match:
            return sanitize_text(match.group(1))
    return None


def extract_property_id(question: str) -> Optional[str]:
    match = re.search(r"\b(P\d{5})\b", question, flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


def extract_month(question: str) -> Optional[str]:
    patterns = [
        r"\b(20\d{2}\-\d{2})\b",
        r"\b(20\d{2}\/\d{2})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(1).replace("/", "-")
    return None


def extract_year(question: str) -> Optional[str]:
    match = re.search(r"\b(20\d{2})\b", question)
    return match.group(1) if match else None


def extract_top_n(question: str, default_n: int) -> int:
    match = re.search(r"\btop\s+(\d+)\b", question, flags=re.IGNORECASE)
    if match:
        return max(1, min(int(match.group(1)), 100))
    return default_n


def is_historical_request(question: str) -> bool:
    q = question.lower()
    historical_terms = [
        "historical",
        "historically",
        "history",
        "over time",
        "all months",
        "every month",
        "trend",
        "monthly trend",
        "across months",
        "across time",
        "last 3 months",
        "last 6 months",
        "last 12 months",
        "month by month",
        "timeline",
    ]
    if any(term in q for term in historical_terms):
        return True
    if extract_month(question) or extract_year(question):
        return True
    return False


def build_market_rent_count_and_detail_queries(
    city: Optional[str],
    rent_status: str,
    max_rows: int,
    historical: bool,
    month_filter: Optional[str] = None,
    year_filter: Optional[str] = None,
) -> Tuple[str, str, str]:
    status_safe = sanitize_text(rent_status).upper()
    city_filter = ""
    if city:
        city_safe = sanitize_text(city)
        city_filter = f" AND lower(city) = lower('{city_safe}')"

    if historical and month_filter:
        base_where = f"""
WHERE upper(coalesce(rent_status, '')) = '{status_safe}'
  AND substr(CAST(month AS varchar), 1, 7) = '{month_filter}'
  {city_filter}
""".strip()

        count_sql = f"""
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_market_rent_predictions
{base_where}
""".strip()

        detail_sql = f"""
SELECT property_id,
       month,
       city,
       CAST(current_portfolio_rent AS DOUBLE) AS current_portfolio_rent,
       CAST(predicted_market_rent AS DOUBLE) AS predicted_market_rent,
       CAST(recommended_rent AS DOUBLE) AS recommended_rent,
       CAST(rent_gap AS DOUBLE) AS rent_gap,
       CAST(rent_gap_pct AS DOUBLE) AS rent_gap_pct,
       rent_status,
       CAST(confidence_score AS DOUBLE) AS confidence_score,
       CAST(annual_rent_opportunity AS DOUBLE) AS annual_rent_opportunity
FROM output_market_rent_predictions
{base_where}
ORDER BY ABS(CAST(rent_gap AS DOUBLE)) DESC
LIMIT {max_rows}
""".strip()
        return count_sql, detail_sql, "historical_month"

    if historical and year_filter:
        base_where = f"""
WHERE upper(coalesce(rent_status, '')) = '{status_safe}'
  AND substr(CAST(month AS varchar), 1, 4) = '{year_filter}'
  {city_filter}
""".strip()

        count_sql = f"""
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_market_rent_predictions
{base_where}
""".strip()

        detail_sql = f"""
SELECT property_id,
       month,
       city,
       CAST(current_portfolio_rent AS DOUBLE) AS current_portfolio_rent,
       CAST(predicted_market_rent AS DOUBLE) AS predicted_market_rent,
       CAST(recommended_rent AS DOUBLE) AS recommended_rent,
       CAST(rent_gap AS DOUBLE) AS rent_gap,
       CAST(rent_gap_pct AS DOUBLE) AS rent_gap_pct,
       rent_status,
       CAST(confidence_score AS DOUBLE) AS confidence_score,
       CAST(annual_rent_opportunity AS DOUBLE) AS annual_rent_opportunity
FROM output_market_rent_predictions
{base_where}
ORDER BY CAST(month AS varchar) DESC, ABS(CAST(rent_gap AS DOUBLE)) DESC
LIMIT {max_rows}
""".strip()
        return count_sql, detail_sql, "historical_year"

    if historical:
        base_where = f"""
WHERE upper(coalesce(rent_status, '')) = '{status_safe}'
  {city_filter}
""".strip()

        count_sql = f"""
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_market_rent_predictions
{base_where}
""".strip()

        detail_sql = f"""
SELECT property_id,
       month,
       city,
       CAST(current_portfolio_rent AS DOUBLE) AS current_portfolio_rent,
       CAST(predicted_market_rent AS DOUBLE) AS predicted_market_rent,
       CAST(recommended_rent AS DOUBLE) AS recommended_rent,
       CAST(rent_gap AS DOUBLE) AS rent_gap,
       CAST(rent_gap_pct AS DOUBLE) AS rent_gap_pct,
       rent_status,
       CAST(confidence_score AS DOUBLE) AS confidence_score,
       CAST(annual_rent_opportunity AS DOUBLE) AS annual_rent_opportunity
FROM output_market_rent_predictions
{base_where}
ORDER BY CAST(month AS varchar) DESC, ABS(CAST(rent_gap AS DOUBLE)) DESC
LIMIT {max_rows}
""".strip()
        return count_sql, detail_sql, "historical_all"

    count_sql = f"""
WITH latest AS (
    SELECT property_id, MAX(month) AS latest_month
    FROM output_market_rent_predictions
    GROUP BY property_id
)
SELECT COUNT(DISTINCT m.property_id) AS total_count
FROM output_market_rent_predictions m
JOIN latest l
  ON m.property_id = l.property_id
 AND m.month = l.latest_month
WHERE upper(coalesce(m.rent_status, '')) = '{status_safe}'
  {city_filter.replace('city', 'm.city')}
""".strip()

    detail_sql = f"""
WITH latest AS (
    SELECT property_id, MAX(month) AS latest_month
    FROM output_market_rent_predictions
    GROUP BY property_id
)
SELECT m.property_id,
       m.month,
       m.city,
       CAST(m.current_portfolio_rent AS DOUBLE) AS current_portfolio_rent,
       CAST(m.predicted_market_rent AS DOUBLE) AS predicted_market_rent,
       CAST(m.recommended_rent AS DOUBLE) AS recommended_rent,
       CAST(m.rent_gap AS DOUBLE) AS rent_gap,
       CAST(m.rent_gap_pct AS DOUBLE) AS rent_gap_pct,
       m.rent_status,
       CAST(m.confidence_score AS DOUBLE) AS confidence_score,
       CAST(m.annual_rent_opportunity AS DOUBLE) AS annual_rent_opportunity
FROM output_market_rent_predictions m
JOIN latest l
  ON m.property_id = l.property_id
 AND m.month = l.latest_month
WHERE upper(coalesce(m.rent_status, '')) = '{status_safe}'
  {city_filter.replace('city', 'm.city')}
ORDER BY ABS(CAST(m.rent_gap AS DOUBLE)) DESC
LIMIT {max_rows}
""".strip()

    return count_sql, detail_sql, "latest_snapshot"


def detect_query_plan(question: str, default_max_rows: int) -> Dict[str, Any]:
    q = question.strip()
    q_lower = q.lower()
    city = extract_city(q)
    property_id = extract_property_id(q)
    month_filter = extract_month(q)
    year_filter = extract_year(q)
    historical = is_historical_request(q)
    max_rows = extract_top_n(q, default_max_rows)

    # MARKET RENT WITH CITY
    if city and ("under-rented" in q_lower or "under rented" in q_lower):
        count_sql, detail_sql, time_mode = build_market_rent_count_and_detail_queries(
            city=city,
            rent_status="UNDER_RENTED",
            max_rows=max_rows,
            historical=historical,
            month_filter=month_filter,
            year_filter=year_filter,
        )
        return {
            "mode": "market_rent_under_rented_city",
            "table": "output_market_rent_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": time_mode,
            "city": city,
            "max_rows": max_rows,
        }

    if city and ("over-rented" in q_lower or "over rented" in q_lower):
        count_sql, detail_sql, time_mode = build_market_rent_count_and_detail_queries(
            city=city,
            rent_status="OVER_RENTED",
            max_rows=max_rows,
            historical=historical,
            month_filter=month_filter,
            year_filter=year_filter,
        )
        return {
            "mode": "market_rent_over_rented_city",
            "table": "output_market_rent_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": time_mode,
            "city": city,
            "max_rows": max_rows,
        }

    # MARKET RENT DASHBOARD / GENERIC
    if ("top 15 under-rented properties" in q_lower) or ("top under-rented properties" in q_lower):
        count_sql, detail_sql, time_mode = build_market_rent_count_and_detail_queries(
            city=None,
            rent_status="UNDER_RENTED",
            max_rows=15,
            historical=False,
        )
        return {
            "mode": "market_rent_under_rented_all",
            "table": "output_market_rent_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": time_mode,
            "city": None,
            "max_rows": 15,
        }

    if ("latest month top 15 properties by rent gap" in q_lower) or ("latest month top 15 properties by rent gap with current and market rent" in q_lower):
        count_sql, detail_sql, time_mode = build_market_rent_count_and_detail_queries(
            city=None,
            rent_status="UNDER_RENTED",
            max_rows=15,
            historical=False,
        )
        return {
            "mode": "market_rent_under_rented_all",
            "table": "output_market_rent_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": time_mode,
            "city": None,
            "max_rows": 15,
        }

    # NOI FORECAST SINGLE PROPERTY
    if property_id and ("forecast" in q_lower or "noi" in q_lower):
        if month_filter:
            detail_sql = f"""
SELECT property_id,
       forecast_month,
       CAST(predicted_noi AS DOUBLE) AS predicted_noi,
       CAST(lower_bound AS DOUBLE) AS lower_bound,
       CAST(upper_bound AS DOUBLE) AS upper_bound
FROM output_noi_forecast_ml
WHERE upper(property_id) = '{property_id}'
  AND substr(CAST(forecast_month AS varchar), 1, 7) = '{month_filter}'
ORDER BY forecast_month
""".strip()

            count_sql = f"""
SELECT COUNT(*) AS total_count
FROM output_noi_forecast_ml
WHERE upper(property_id) = '{property_id}'
  AND substr(CAST(forecast_month AS varchar), 1, 7) = '{month_filter}'
""".strip()

            time_mode = "forecast_month"
        else:
            detail_sql = f"""
SELECT property_id,
       forecast_month,
       CAST(predicted_noi AS DOUBLE) AS predicted_noi,
       CAST(lower_bound AS DOUBLE) AS lower_bound,
       CAST(upper_bound AS DOUBLE) AS upper_bound
FROM output_noi_forecast_ml
WHERE upper(property_id) = '{property_id}'
ORDER BY forecast_month
""".strip()

            count_sql = f"""
SELECT COUNT(*) AS total_count
FROM output_noi_forecast_ml
WHERE upper(property_id) = '{property_id}'
""".strip()

            time_mode = "forecast_horizon"

        return {
            "mode": "noi_forecast_property",
            "table": "output_noi_forecast_ml",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "property_id": property_id,
            "time_mode": time_mode,
            "max_rows": max_rows,
        }

    # PORTFOLIO NOI KPI
    if ("portfolio noi" in q_lower or "total predicted noi" in q_lower or "forecast portfolio noi" in q_lower):
        if month_filter:
            detail_sql = f"""
SELECT substr(CAST(forecast_month AS varchar), 1, 7) AS forecast_month,
       CAST(SUM(CAST(predicted_noi AS DOUBLE)) AS DOUBLE) AS total_predicted_noi
FROM output_noi_forecast_ml
WHERE substr(CAST(forecast_month AS varchar), 1, 7) = '{month_filter}'
GROUP BY substr(CAST(forecast_month AS varchar), 1, 7)
""".strip()
            time_mode = "forecast_month"
        else:
            detail_sql = """
SELECT CAST(SUM(CAST(predicted_noi AS DOUBLE)) AS DOUBLE) AS total_predicted_noi
FROM output_noi_forecast_ml
""".strip()
            time_mode = "aggregate"

        count_sql = """
SELECT COUNT(*) AS total_count
FROM output_noi_forecast_ml
""".strip()

        return {
            "mode": "portfolio_noi_kpi",
            "table": "output_noi_forecast_ml",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": time_mode,
            "max_rows": max_rows,
        }

    # NOI RANKED PROPERTIES
    if ("top 15 properties by forecast noi" in q_lower) or ("top 15 highest noi properties" in q_lower):
        max_rows = 15

    if ("top" in q_lower or "highest" in q_lower or "lowest" in q_lower) and "noi" in q_lower and not property_id:
        descending = "lowest" not in q_lower
        direction = "DESC" if descending else "ASC"

        if month_filter:
            base_where = f"WHERE substr(CAST(forecast_month AS varchar), 1, 7) = '{month_filter}'"
            detail_sql = f"""
SELECT property_id,
       forecast_month,
       CAST(predicted_noi AS DOUBLE) AS predicted_noi,
       CAST(lower_bound AS DOUBLE) AS lower_bound,
       CAST(upper_bound AS DOUBLE) AS upper_bound
FROM output_noi_forecast_ml
{base_where}
ORDER BY CAST(predicted_noi AS DOUBLE) {direction}
LIMIT {max_rows}
""".strip()

            count_sql = f"""
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_noi_forecast_ml
{base_where}
""".strip()
            time_mode = "forecast_month"
        else:
            detail_sql = f"""
WITH latest_forecast AS (
    SELECT MAX(forecast_month) AS latest_month
    FROM output_noi_forecast_ml
)
SELECT n.property_id,
       n.forecast_month,
       CAST(n.predicted_noi AS DOUBLE) AS predicted_noi,
       CAST(n.lower_bound AS DOUBLE) AS lower_bound,
       CAST(n.upper_bound AS DOUBLE) AS upper_bound
FROM output_noi_forecast_ml n
JOIN latest_forecast l
  ON n.forecast_month = l.latest_month
ORDER BY CAST(n.predicted_noi AS DOUBLE) {direction}
LIMIT {max_rows}
""".strip()

            count_sql = """
WITH latest_forecast AS (
    SELECT MAX(forecast_month) AS latest_month
    FROM output_noi_forecast_ml
)
SELECT COUNT(DISTINCT n.property_id) AS total_count
FROM output_noi_forecast_ml n
JOIN latest_forecast l
  ON n.forecast_month = l.latest_month
""".strip()
            time_mode = "latest_forecast_month"

        return {
            "mode": "noi_ranked_properties",
            "table": "output_noi_forecast_ml",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": time_mode,
            "ranking": "highest" if descending else "lowest",
            "max_rows": max_rows,
        }

    # MAINTENANCE DISTRIBUTION - ACTUAL COLUMNS
    if "maintenance" in q_lower and ("distribution" in q_lower or "risk distribution" in q_lower):
        count_sql = """
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_maintenance_risk_predictions
""".strip()

        detail_sql = """
SELECT COALESCE(UPPER(predicted_risk_band), 'UNKNOWN') AS predicted_risk_band,
       COUNT(DISTINCT property_id) AS property_count
FROM output_maintenance_risk_predictions
GROUP BY COALESCE(UPPER(predicted_risk_band), 'UNKNOWN')
ORDER BY property_count DESC
""".strip()

        return {
            "mode": "maintenance_risk_distribution",
            "table": "output_maintenance_risk_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": "current_snapshot",
            "max_rows": max_rows,
        }

    # MAINTENANCE HIGH RISK - ACTUAL COLUMNS
    if ("high-risk" in q_lower or "high risk" in q_lower) and (
        "maintenance" in q_lower or "property" in q_lower or "properties" in q_lower or "system" in q_lower
    ):
        count_sql = """
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_maintenance_risk_predictions
WHERE COALESCE(UPPER(predicted_risk_band), 'UNKNOWN') = 'HIGH'
""".strip()

        detail_sql = f"""
SELECT property_id,
       month,
       city,
       property_type,
       system_type,
       CAST(predicted_risk_score AS DOUBLE) AS predicted_risk_score,
       COALESCE(UPPER(predicted_risk_band), 'UNKNOWN') AS predicted_risk_band,
       CAST(estimated_cost_impact AS DOUBLE) AS estimated_cost_impact,
       alert_flag
FROM output_maintenance_risk_predictions
WHERE COALESCE(UPPER(predicted_risk_band), 'UNKNOWN') = 'HIGH'
ORDER BY CAST(predicted_risk_score AS DOUBLE) DESC, CAST(estimated_cost_impact AS DOUBLE) DESC
LIMIT {max_rows}
""".strip()

        return {
            "mode": "maintenance_high_risk_assets",
            "table": "output_maintenance_risk_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": "current_snapshot",
            "max_rows": max_rows,
        }

    # MAINTENANCE LOW RISK
    if ("lowest-risk" in q_lower or "lowest risk" in q_lower) and (
        "maintenance" in q_lower or "property" in q_lower or "properties" in q_lower or "system" in q_lower
    ):
        count_sql = """
SELECT COUNT(DISTINCT property_id) AS total_count
FROM output_maintenance_risk_predictions
""".strip()

        detail_sql = f"""
SELECT property_id,
       month,
       city,
       property_type,
       system_type,
       CAST(predicted_risk_score AS DOUBLE) AS predicted_risk_score,
       COALESCE(UPPER(predicted_risk_band), 'UNKNOWN') AS predicted_risk_band,
       CAST(estimated_cost_impact AS DOUBLE) AS estimated_cost_impact,
       alert_flag
FROM output_maintenance_risk_predictions
ORDER BY CAST(predicted_risk_score AS DOUBLE) ASC, CAST(estimated_cost_impact AS DOUBLE) ASC
LIMIT {max_rows}
""".strip()

        return {
            "mode": "maintenance_low_risk_assets",
            "table": "output_maintenance_risk_predictions",
            "count_sql": count_sql,
            "detail_sql": detail_sql,
            "time_mode": "current_snapshot",
            "max_rows": max_rows,
        }

    return {
        "mode": "llm_sql",
        "table": "unknown",
        "count_sql": None,
        "detail_sql": None,
        "time_mode": "unknown",
        "max_rows": max_rows,
    }


def generate_sql_with_bedrock(question: str, max_rows: int) -> str:
    prompt = f"""
You are an Athena SQL generator for a real-estate analytics copilot.
Return ONLY executable Athena SQL. Do not add markdown or explanation.

Database: {DATABASE}

Tables:
1) output_market_rent_predictions
- property_id
- month
- city
- current_portfolio_rent
- predicted_market_rent
- recommended_rent
- rent_gap
- rent_gap_pct
- rent_status
- confidence_score
- annual_rent_opportunity

2) output_noi_forecast_ml
- property_id
- forecast_month
- predicted_noi
- lower_bound
- upper_bound

3) output_maintenance_risk_predictions
- property_id
- month
- city
- property_type
- system_type
- repair_cost
- asset_age
- avg_repair_cost_3m
- predicted_probability
- predicted_risk_score
- predicted_risk_band
- estimated_cost_impact
- alert_flag

Rules:
- Default LIMIT {max_rows} unless the user explicitly asks for a total or KPI.
- For market rent without a time filter, use latest available month per property.
- For single-property NOI forecast, return the full forecast horizon.
- For maintenance risk, use predicted_risk_band and predicted_risk_score, not risk_level or asset_type.
- Prefer CAST(... AS DOUBLE) for numeric fields.
- Use only the listed tables and columns.

User question:
{question}
"""
    sql = call_bedrock(prompt, max_tokens=450)
    return sql.replace("```sql", "").replace("```", "").strip().rstrip(";")


def summarize_results(
    question: str,
    data: List[Dict[str, Any]],
    mode: str,
    total_count: Optional[int] = None,
    time_mode: str = "unknown",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    context = context or {}

    if not data and (total_count is None or total_count == 0):
        return "No matching data found."

    if mode in {"market_rent_under_rented_city", "market_rent_over_rented_city", "market_rent_under_rented_all"}:
        city = context.get("city")
        is_under = "under" in mode
        status = "under-rented" if is_under else "over-rented"

        prop_ids = [row.get("property_id") for row in data if row.get("property_id")]
        top_n_list = ", ".join(prop_ids[:10]) if prop_ids else "N/A"

        gap_pcts = [to_float(row.get("rent_gap_pct")) for row in data]
        gap_pcts = [x for x in gap_pcts if x is not None]
        avg_gap_pct = sum(gap_pcts) / len(gap_pcts) if gap_pcts else None

        rent_gaps = []
        for row in data:
            rg = to_float(row.get("rent_gap"))
            if rg is not None:
                rent_gaps.append((row.get("property_id"), rg))

        biggest_gap_property = None
        biggest_gap_value = None
        if rent_gaps:
            biggest_gap_property, biggest_gap_value = max(rent_gaps, key=lambda x: abs(x[1]))

        annual_opps = [to_float(row.get("annual_rent_opportunity")) for row in data]
        annual_opps = [x for x in annual_opps if x is not None]
        total_opp_preview = sum(annual_opps) if annual_opps else None

        if city:
            msg = f"**{city} has {total_count or len(prop_ids)} {status} properties in the latest available month per property.**\n"
        else:
            msg = f"**Latest month snapshot shows {total_count or len(prop_ids)} {status} properties across the portfolio.**\n"

        msg += f"- Showing top **{len(data)}** properties by largest rent gap\n"
        msg += f"- Top properties returned: **{top_n_list}**\n"

        if biggest_gap_property and biggest_gap_value is not None:
            if is_under:
                msg += f"- Largest pricing uplift opportunity: **{biggest_gap_property}** with a rent gap of **${abs(biggest_gap_value):,.0f}**\n"
            else:
                msg += f"- Most exposed property: **{biggest_gap_property}** with a rent premium of **${abs(biggest_gap_value):,.0f}**\n"

        if avg_gap_pct is not None:
            if is_under:
                msg += f"- Average gap in shown results: **{abs(avg_gap_pct):.1%} below market**\n"
            else:
                msg += f"- Average gap in shown results: **{abs(avg_gap_pct):.1%} above market**\n"

        if total_opp_preview is not None and is_under:
            msg += f"- Business insight: portfolio is leaving substantial money on the table with meaningful underpricing across top underperformers - immediate rent optimization could unlock significant revenue growth."
        else:
            msg += "- Business insight: materially over-market properties may face higher renewal pressure and occupancy risk unless supported by strong tenant demand or asset premium."

        return msg

    if mode == "noi_forecast_property":
        property_id = context.get("property_id", "the property")
        months = [row.get("forecast_month") for row in data if row.get("forecast_month")]
        values = [to_float(row.get("predicted_noi")) for row in data]
        values = [x for x in values if x is not None]
        lower_vals = [to_float(row.get("lower_bound")) for row in data]
        lower_vals = [x for x in lower_vals if x is not None]
        upper_vals = [to_float(row.get("upper_bound")) for row in data]
        upper_vals = [x for x in upper_vals if x is not None]

        if values and months:
            avg_noi = sum(values) / len(values)
            best_noi = max(values)
            worst_noi = min(values)

            msg = f"**NOI forecast for {property_id}**\n"
            if time_mode == "forecast_month":
                msg += f"- Matching forecast rows for the requested month: **{len(data)}**\n"
                msg += f"- Forecast month: **{months[0]}**\n"
            else:
                msg += f"- Forecast horizon available: **{len(data)} months**\n"
                msg += f"- Forecast period: **{months[0]} to {months[-1]}**\n"

            msg += f"- Average predicted NOI: **${avg_noi:,.0f}**\n"
            msg += f"- Predicted NOI range: **${worst_noi:,.0f} to ${best_noi:,.0f}**\n"
            if lower_vals and upper_vals:
                msg += f"- Confidence band across the horizon: **${min(lower_vals):,.0f} to ${max(upper_vals):,.0f}**\n"
            msg += "- Business insight: this forecast gives a forward view of expected income performance for budgeting, asset planning, and scenario analysis."
            return msg

        return f"Forecast data found for **{property_id}**."

    if mode == "portfolio_noi_kpi":
        total_noi = to_float(data[0].get("total_predicted_noi")) if data else None
        forecast_month = data[0].get("forecast_month") if data else None
        if total_noi is not None:
            msg = "**Portfolio predicted NOI**\n"
            if forecast_month:
                msg += f"- Forecast month: **{forecast_month}**\n"
            msg += f"- Total forecast NOI: **${total_noi:,.0f}**\n"
            msg += "- Business insight: this is the projected portfolio income baseline from the current forecast table."
            return msg
        return "Portfolio NOI result returned."

    if mode == "noi_ranked_properties":
        ranking = context.get("ranking", "highest")
        prop_ids = [row.get("property_id") for row in data if row.get("property_id")]
        top_list = ", ".join(prop_ids[:10]) if prop_ids else "N/A"
        values = [to_float(row.get("predicted_noi")) for row in data]
        values = [x for x in values if x is not None]
        month_vals = [row.get("forecast_month") for row in data if row.get("forecast_month")]
        forecast_month = month_vals[0] if month_vals else None

        if values:
            avg_noi = sum(values) / len(values)
            msg = f"**Properties with the {ranking} forecast NOI**\n"
            msg += f"- Total matching properties: **{total_count or len(prop_ids)}**\n"
            msg += f"- Showing top **{len(data)}** properties\n"
            if forecast_month:
                msg += f"- Forecast month used: **{forecast_month}**\n"
            msg += f"- Top properties returned: **{top_list}**\n"
            msg += f"- Average predicted NOI in shown results: **${avg_noi:,.0f}**\n"
            if ranking == "highest":
                msg += "- Business insight: these properties appear to be the strongest forecast contributors in the selected forecast window."
            else:
                msg += "- Business insight: these properties may warrant closer review, as they are forecast to contribute comparatively lower NOI."
            return msg
        return "Ranked NOI results returned."

    if mode == "maintenance_risk_distribution":
        parts = []
        high_count = 0
        total_props = total_count or 0

        for row in data:
            level = (row.get("predicted_risk_band") or "UNKNOWN").upper()
            cnt = to_int(row.get("property_count"))
            parts.append(f"**{level}**: {cnt}")
            if level == "HIGH":
                high_count = cnt

        msg = "**Maintenance risk distribution across the portfolio**\n"
        msg += f"- {', '.join(parts)}\n"
        msg += f"- Total properties covered: **{total_props}**\n"
        if total_props > 0:
            msg += f"- High-risk share: **{(high_count / total_props):.1%}**\n"
        msg += "- Business insight: this helps prioritize preventive maintenance, inspections, and maintenance budget allocation."
        return msg

    if mode == "maintenance_high_risk_assets":
        props = [row.get("property_id") for row in data if row.get("property_id")]
        top_list = ", ".join(props[:10]) if props else "N/A"

        risk_scores = [to_float(row.get("predicted_risk_score")) for row in data]
        risk_scores = [x for x in risk_scores if x is not None]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else None
        max_risk = max(risk_scores) if risk_scores else None

        systems = list({row.get("system_type") for row in data if row.get("system_type")})
        systems_str = ", ".join(systems[:5]) if systems else "N/A"

        msg = "**High-risk maintenance properties**\n"
        msg += f"- Total high-risk properties: **{total_count or 0}**\n"
        msg += f"- Showing top **{len(data)}** by predicted risk score\n"
        msg += f"- Top properties returned: **{top_list}**\n"
        msg += f"- Systems represented: **{systems_str}**\n"
        msg += "- Business insight: these properties and systems should be prioritized first for inspection and preventive maintenance action."
        return msg

    if mode == "maintenance_low_risk_assets":
        props = [row.get("property_id") for row in data if row.get("property_id")]
        top_list = ", ".join(props[:10]) if props else "N/A"

        risk_scores = [to_float(row.get("predicted_risk_score")) for row in data]
        risk_scores = [x for x in risk_scores if x is not None]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else None
        min_risk = min(risk_scores) if risk_scores else None

        msg = "**Lowest-risk maintenance properties**\n"
        msg += f"- Total properties assessed: **{total_count or 0}**\n"
        msg += f"- Showing top **{len(data)}** lowest-risk properties\n"
        msg += f"- Properties returned: **{top_list}**\n"
        msg += "- Business insight: these assets currently appear lower priority for urgent intervention."
        return msg

    preview = json.dumps(data[:3], default=str)
    prompt = f"""
You are a real-estate analytics copilot.
Write a concise markdown answer with:
- 1 headline sentence
- 4 bullet points
- 1 business insight line

User question:
{question}

Returned rows:
{len(data)}

Results preview:
{preview}
"""
    return call_bedrock(prompt, max_tokens=260)


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return api_response(200, {"ok": True})

    try:
        body = parse_event_body(event)
        question = (body.get("question") or "").strip()
        include_details = bool(body.get("include_details", False))
        default_max_rows = int(body.get("max_rows") or DEFAULT_MAX_ROWS)
        default_max_rows = max(1, min(default_max_rows, 100))

        if not question:
            return api_response(400, {"error": "question required"})

        plan = detect_query_plan(question, default_max_rows)
        mode = plan["mode"]

        if mode == "llm_sql":
            sql = generate_sql_with_bedrock(question, plan["max_rows"])
            data = run_athena_query(sql)
            answer = summarize_results(
                question=question,
                data=data,
                mode=mode,
                total_count=len(data),
                time_mode="llm_generated",
                context=plan,
            )
            return api_response(200, {
                "question": question,
                "answer": answer,
                "sql": sql,
                "row_count": len(data),
                "total_count": len(data),
                "mode": mode,
                "time_mode": "llm_generated",
                "data": data if include_details else [],
            })

        count_rows = run_athena_query(plan["count_sql"])
        detail_rows = run_athena_query(plan["detail_sql"])

        total_count = 0
        if count_rows:
            total_count = to_int(count_rows[0].get("total_count", 0))

        answer = summarize_results(
            question=question,
            data=detail_rows,
            mode=mode,
            total_count=total_count,
            time_mode=plan.get("time_mode", "unknown"),
            context=plan,
        )

        return api_response(200, {
            "question": question,
            "answer": answer,
            "sql": plan["detail_sql"],
            "count_sql": plan["count_sql"],
            "row_count": len(detail_rows),
            "total_count": total_count,
            "mode": mode,
            "time_mode": plan.get("time_mode", "unknown"),
            "data": detail_rows if include_details else [],
        })

    except Exception as exc:
        return api_response(500, {"error": str(exc)})