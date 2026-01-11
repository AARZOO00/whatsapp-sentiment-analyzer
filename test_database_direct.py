#!/usr/bin/env python3
"""Direct unit test of database functions."""
import json
from backend.database import init_db, insert_message, query_messages, get_stats, clear_all_messages
from datetime import datetime

print("Testing database functions directly...")
print("=" * 60)

# Initialize
init_db()
clear_all_messages()
print("✓ Database initialized")

# Insert test messages
insert_message(
    msg_id="test_1",
    job_id="job_1",
    timestamp="2024-08-15 10:30",
    sender="Alice",
    text="This is awesome!",
    translated_text=None,
    language="en",
    vader_score=0.8,
    textblob_score=0.75,
    ensemble_score=0.775,
    ensemble_label="Positive",
    emotions=json.dumps({"joy": 0.9, "sadness": 0.0}),
    keywords=json.dumps(["awesome"]),
)

insert_message(
    msg_id="test_2",
    job_id="job_1",
    timestamp="2024-08-15 10:31",
    sender="Bob",
    text="I'm doing great!",
    translated_text=None,
    language="en",
    vader_score=0.7,
    textblob_score=0.65,
    ensemble_score=0.675,
    ensemble_label="Positive",
    emotions=json.dumps({"joy": 0.8, "sadness": 0.0}),
    keywords=json.dumps(["great"]),
)

insert_message(
    msg_id="test_3",
    job_id="job_1",
    timestamp="2024-08-15 10:45",
    sender="Alice",
    text="That was terrible!",
    translated_text=None,
    language="en",
    vader_score=-0.7,
    textblob_score=-0.65,
    ensemble_score=-0.675,
    ensemble_label="Negative",
    emotions=json.dumps({"joy": 0.0, "sadness": 0.9}),
    keywords=json.dumps(["terrible"]),
)

print("✓ 3 messages inserted")

# Test query all
messages, total = query_messages(limit=10, offset=0)
print(f"✓ Query all: {total} messages found")
assert len(messages) == 3

# Test filter by sender
messages, total = query_messages(sender="Alice", limit=10, offset=0)
print(f"✓ Filter by sender (Alice): {total} messages")
assert total == 2

# Test filter by sentiment
messages, total = query_messages(sentiment="Positive", limit=10, offset=0)
print(f"✓ Filter by sentiment (Positive): {total} messages")
assert total == 2

messages, total = query_messages(sentiment="Negative", limit=10, offset=0)
print(f"✓ Filter by sentiment (Negative): {total} messages")
assert total == 1

# Test keyword search
messages, total = query_messages(keyword="awesome", limit=10, offset=0)
print(f"✓ Keyword search ('awesome'): {total} messages")
assert total == 1

# Test stats
stats = get_stats()
print(f"✓ Stats computed:")
print(f"    - Total: {stats['total_messages']}")
print(f"    - Sentiment dist: {stats['sentiment_distribution']}")
print(f"    - Avg sentiment: {stats['average_sentiment_score']:.2f}")
print(f"    - Top participants: {stats['top_participants']}")

# Test stats with filter
stats = get_stats(sender="Alice")
print(f"✓ Stats for Alice: {stats['total_messages']} messages")

print("\n" + "=" * 60)
print("DATABASE TESTS: ALL PASSED ✓")
print("=" * 60)
