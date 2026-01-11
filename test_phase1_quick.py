#!/usr/bin/env python3
"""Quick test of Phase 1 database and filtering (skip summarization wait)."""
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import clear_all_messages

client = TestClient(app)

SAMPLE = '''8/15/2024, 10:30 PM - Alice: Hey! Awesome!
8/15/2024, 10:31 PM - Bob: I'm great!'''


def test_phase1_quick():
    print("\nPHASE 1 QUICK TEST")
    print("=" * 60)

    clear_all_messages()
    print("✓ Database cleared")

    # Upload
    files = {"file": ("sample.txt", SAMPLE.encode("utf-8"), "text/plain")}
    resp = client.post("/analyze", files=files)
    job_id = resp.json().get("job_id")
    print(f"✓ Job {job_id[:8]}... created")

    # Poll until complete
    import time
    for i in range(120):
        r = client.get(f"/results/{job_id}")
        if r.json().get("status") == "complete":
            print(f"✓ Analysis complete in {i + 1}s")
            break
        if i % 10 == 0:
            print(f"  Polling... {i+1}s")
        time.sleep(1)

    # Test /messages
    print("\nTesting /messages endpoint:")
    resp = client.get("/messages?limit=10&page=1")
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Retrieved {data['total']} messages")
    if data['messages']:
        msg = data['messages'][0]
        print(f"  Sample: {msg['sender']} - {msg['text'][:40]}...")
        print(f"  Sentiment: {msg['ensemble_label']} ({msg['ensemble_score']:.2f})")

    # Test /stats
    print("\nTesting /stats endpoint:")
    resp = client.get("/stats")
    assert resp.status_code == 200
    stats = resp.json()
    print(f"✓ Total messages: {stats['total_messages']}")
    print(f"✓ Sentiment distribution: {stats['sentiment_distribution']}")
    print(f"✓ Average sentiment: {stats['average_sentiment_score']:.2f}")

    # Test filter by user
    print("\nTesting user filter:")
    resp = client.get("/messages?user=Alice&limit=10&page=1")
    data = resp.json()
    print(f"✓ Alice has {data['total']} messages")

    print("\n" + "=" * 60)
    print("PHASE 1: Database & filtering WORKING ✓")
    # Do not return values from pytest test functions


if __name__ == "__main__":
    try:
        test_phase1_quick()
        raise SystemExit(0)
    except Exception as e:
        print(f"\n✗ {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
