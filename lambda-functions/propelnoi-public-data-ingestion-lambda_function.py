import os
import json
import boto3
import urllib.request
from datetime import datetime, timezone

s3 = boto3.client("s3")

BUCKET = os.environ["BUCKET_NAME"]
CITY_URLS = json.loads(os.environ["INSIDEAIRBNB_CITY_URLS"])

# Official World Bank indicator CSV file for FP.CPI.TOTL.ZG
WORLD_BANK_CSV_URL = "https://data360files.worldbank.org/data360-data/data/WB_WDI/WB_WDI_FP_CPI_TOTL_ZG.csv"


def upload_bytes_to_s3(content: bytes, key: str, content_type: str = None):
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=content,
        **extra_args
    )


def download_bytes(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def lambda_handler(event, context):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    results = {
        "date": today,
        "uploads": [],
        "errors": []
    }

    try:
        # 1) World Bank inflation CSV
        wb_content = download_bytes(WORLD_BANK_CSV_URL, timeout=60)

        wb_key = f"raw/economic/worldbank/inflation_{today}.csv"
        upload_bytes_to_s3(wb_content, wb_key, "text/csv")
        results["uploads"].append(wb_key)

        # 2) Inside Airbnb city files
        for city, url in CITY_URLS.items():
            try:
                city_content = download_bytes(url, timeout=120)
                city_key = f"raw/market/insideairbnb/{city}/listings_{today}.csv.gz"
                upload_bytes_to_s3(city_content, city_key, "application/gzip")
                results["uploads"].append(city_key)
            except Exception as city_error:
                results["errors"].append({
                    "city": city,
                    "error": str(city_error)
                })

        if results["errors"]:
            return {
                "statusCode": 207,
                "body": json.dumps({
                    "message": "Public data ingestion completed with partial success",
                    "results": results
                })
            }

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Public data ingestion completed successfully",
                "results": results
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Public data ingestion failed",
                "error": str(e),
                "results": results
            })
        }