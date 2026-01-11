#!/usr/bin/env python3
"""Integration test using FastAPI TestClient to avoid running Uvicorn.
This tests /analyze and /results endpoints end-to-end within the process.
"""
import time
from fastapi.testclient import TestClient
from backend.main import app, job_store

client = TestClient(app)

SAMPLE = '''8/15/2024, 10:30 PM - Alice: Hey everyone! This is awesome!
8/15/2024, 10:31 PM - Bob: I'm doing great, thanks for asking!
8/15/2024, 10:32 PM - Charlie: Same here! This is wonderful!'''


def run_test():
    print("[TEST] Posting sample chat to /analyze")
    files = {"file": ("sample.txt", SAMPLE.encode("utf-8"), "text/plain")}
    resp = client.post("/analyze", files=files)
    print("  status_code:", resp.status_code)
    data = resp.json()
    if resp.status_code != 202:
        print("  Error payload:", data)
        return 1

    job_id = data.get("job_id")
    print("  job_id:", job_id)

    # Poll until complete or timeout
    timeout = 60
    start = time.time()
    while True:
        r = client.get(f"/results/{job_id}")
        if r.status_code != 200:
            print("  Results endpoint returned non-200:", r.status_code, r.text)
            return 1
        payload = r.json()
        status = payload.get("status")
        print("  status:", status)
        if status == "complete":
            result = payload.get("result")
            print("  Completed. total_messages:", result.get("total_messages"))
            print("  Overall sentiment:", result.get("overall_sentiment"))
            return 0
        if status == "failed":
            print("  Failed:", payload)
            return 1
        if time.time() - start > timeout:
            print("  Timeout waiting for result")
            return 1
        time.sleep(1)


if __name__ == "__main__":
    exit_code = run_test()
    raise SystemExit(exit_code)
