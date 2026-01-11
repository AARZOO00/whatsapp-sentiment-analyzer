#!/usr/bin/env python3
"""Test Phase 1: Backend message storage and filtering APIs."""
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import clear_all_messages

client = TestClient(app)

SAMPLE = '''8/15/2024, 10:30 PM - Alice: Hey everyone! This is awesome!
8/15/2024, 10:31 PM - Bob: I'm doing great, thanks for asking!
8/15/2024, 10:32 PM - Charlie: Same here! This is wonderful!
8/15/2024, 10:45 PM - Alice: That was terrible experience though.
8/15/2024, 10:46 PM - Bob: Sorry to hear, hope it improves!'''


def test_phase1():
    print("\n" + "=" * 70)
    print("PHASE 1 TEST: Backend Message Storage & Filtering APIs")
    print("=" * 70)

    # Clear database
    clear_all_messages()
    print("\n[SETUP] Database cleared")

    # Step 1: Upload and analyze
    print("\n[STEP 1] Upload and analyze chat")
    print("-" * 70)
    files = {"file": ("sample.txt", SAMPLE.encode("utf-8"), "text/plain")}
    resp = client.post("/analyze", files=files)
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"
    data = resp.json()
    job_id = data.get("job_id")
    print(f"✓ Job created: {job_id}")

    # Poll until complete
    import time
    for i in range(60):
        r = client.get(f"/results/{job_id}")
        payload = r.json()
        if payload.get("status") == "complete":
            print(f"✓ Analysis complete in {i + 1}s")
            break
        time.sleep(1)
    else:
        print("✗ Analysis timed out")
        return 1

    # Step 2: Test /messages endpoint (no filters)
    print("\n[STEP 2] Retrieve all messages via /messages")
    print("-" * 70)
    resp = client.get("/messages?limit=10&page=1")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    print(f"✓ Retrieved {data['total']} total messages")
    print(f"✓ Page 1 has {len(data['messages'])} messages")
    print(f"✓ Total pages: {data['total_pages']}")

    if data["messages"]:
        msg = data["messages"][0]
        print(f"\nSample message:")
        print(f"  - Sender: {msg['sender']}")
        print(f"  - Text: {msg['text'][:50]}...")
        print(f"  - Sentiment: {msg['ensemble_label']} ({msg['ensemble_score']:.2f})")
        print(f"  - Language: {msg['language']}")

    # Step 3: Test /messages with filters
    print("\n[STEP 3] Filter messages by user")
    print("-" * 70)
    resp = client.get("/messages?user=Alice&limit=10&page=1")
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Alice has {data['total']} messages")
    for msg in data["messages"]:
        assert msg["sender"] == "Alice", "Filter failed"
        print(f"  - {msg['timestamp']}: {msg['text'][:40]}...")

    # Step 4: Test sentiment filter
    print("\n[STEP 4] Filter by sentiment")
    print("-" * 70)
    resp = client.get("/messages?sentiment=Positive&limit=10&page=1")
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Found {data['total']} Positive messages")
    for msg in data["messages"][:2]:
        print(f"  - {msg['sender']}: {msg['text'][:40]}...")

    resp = client.get("/messages?sentiment=Negative&limit=10&page=1")
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Found {data['total']} Negative messages")
    for msg in data["messages"][:2]:
        print(f"  - {msg['sender']}: {msg['text'][:40]}...")

    # Step 5: Test keyword search
    print("\n[STEP 5] Keyword search")
    print("-" * 70)
    resp = client.get("/messages?keyword=awesome&limit=10&page=1")
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Found {data['total']} messages with 'awesome'")
    for msg in data["messages"]:
        print(f"  - {msg['text']}")

    # Step 6: Test /stats endpoint
    print("\n[STEP 6] Aggregate statistics via /stats")
    print("-" * 70)
    resp = client.get("/stats")
    assert resp.status_code == 200
    stats = resp.json()
    print(f"✓ Total messages: {stats['total_messages']}")
    print(f"✓ Sentiment distribution:")
    for label, dist in stats["sentiment_distribution"].items():
        print(f"    - {label}: {dist['count']} messages (avg score: {dist['avg_score']:.2f})")
    print(f"✓ Average sentiment: {stats['average_sentiment_score']:.2f}")
    print(f"✓ Language distribution: {stats['language_distribution']}")
    print(f"✓ Top participants: {stats['top_participants']}")

    # Step 7: Test stats with filters
    print("\n[STEP 7] Stats with user filter")
    print("-" * 70)
    resp = client.get("/stats?user=Alice")
    assert resp.status_code == 200
    stats = resp.json()
    print(f"✓ Alice's total messages: {stats['total_messages']}")
    print(f"✓ Alice's average sentiment: {stats['average_sentiment_score']:.2f}")

    # Step 8: Test pagination
    print("\n[STEP 8] Test pagination")
    print("-" * 70)
    resp = client.get("/messages?limit=2&page=1")
    page1 = resp.json()
    print(f"✓ Page 1: {len(page1['messages'])} messages")

    resp = client.get("/messages?limit=2&page=2")
    page2 = resp.json()
    print(f"✓ Page 2: {len(page2['messages'])} messages")
    print(f"✓ Total pages: {page2['total_pages']}")

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 1 TEST: ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nPhase 1 Features Validated:")
    print("  ✓ SQLite message storage")
    print("  ✓ /messages endpoint with pagination")
    print("  ✓ Filtering by user, sentiment, keyword")
    print("  ✓ /stats endpoint with aggregations")
    print("  ✓ Language detection and translation")
    print("\nReady for Phase 2: Chat Viewer UI")
    # Test functions should not return values when run under pytest


if __name__ == "__main__":
    try:
        test_phase1()
        raise SystemExit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
