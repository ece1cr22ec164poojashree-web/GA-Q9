import json
import os
import math

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.json")

with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)

def percentile(values, p):
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] + (values[c] - values[f]) * (k - f)

def handler(request):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }

    if request.method == "OPTIONS":
        return ("", 200, headers)

    if request.method != "POST":
        return (json.dumps({"error": "POST only"}), 405, headers)

    try:
        body = request.get_json()
        regions = body.get("regions", [])
        threshold = body.get("threshold_ms", 0)

        result = {}

        for region in regions:
            records = [r for r in TELEMETRY if r["region"] == region]

            if not records:
                result[region] = {
                    "avg_latency": None,
                    "p95_latency": None,
                    "avg_uptime": None,
                    "breaches": 0
                }
                continue

            latencies = [r["latency_ms"] for r in records]
            uptimes = [r["uptime_pct"] for r in records]

            result[region] = {
                "avg_latency": round(sum(latencies)/len(latencies), 2),
                "p95_latency": round(percentile(latencies, 95), 2),
                "avg_uptime": round(sum(uptimes)/len(uptimes), 3),
                "breaches": sum(1 for r in records if r["latency_ms"] > threshold)
            }

        return (json.dumps(result), 200, headers)

    except Exception as e:
        return (json.dumps({"error": str(e)}), 500, headers)
