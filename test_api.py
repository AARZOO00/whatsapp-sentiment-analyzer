#!/usr/bin/env python3
"""Test the backend API endpoints."""
import requests
import time
import json

api = 'http://127.0.0.1:8000'
sample = '''8/15/2024, 10:30 PM - Alice: Hey everyone! This is awesome!
8/15/2024, 10:31 PM - Bob: I'm doing great, thanks for asking!
8/15/2024, 10:32 PM - Charlie: Same here! This is wonderful!
8/15/2024, 10:33 PM - Alice: That's wonderful! I'm so happy!'''

print("=" * 60)
print("Testing WhatsApp Sentiment Analyzer API")
print("=" * 60)

try:
    # Test 1: Check API health
    print("\n[TEST 1] Checking API health...")
    r = requests.get(f'{api}/docs')
    print(f"  Status: {r.status_code} - API is running!")

    # Test 2: Upload and analyze
    print("\n[TEST 2] Uploading chat file...")
    r = requests.post(f'{api}/analyze', files={'file': ('test.txt', sample.encode())})
    print(f"  Status: {r.status_code}")
    data = r.json()
    if 'error' in data:
        print(f"  ERROR: {data['error']}")
    else:
        job_id = data.get('job_id')
        print(f"  Job ID: {job_id}")

        # Test 3: Poll results
        print("\n[TEST 3] Polling for results...")
        for i in range(10):
            time.sleep(1)
            res = requests.get(f'{api}/results/{job_id}')
            status_data = res.json()
            status = status_data.get('status')
            print(f"  Attempt {i+1}: {status}")
            
            if status == 'complete':
                result = status_data['result']
                print("\n[SUCCESS] Analysis Complete!")
                print(f"  Total Messages: {result['total_messages']}")
                print(f"  Overall Sentiment: {result['overall_sentiment']['ensemble_label']}")
                print(f"  Confidence: {result['overall_sentiment']['ensemble_score']:.3f}")
                print(f"  Primary Language: {result['primary_language']}")
                print(f"  Summary: {result['summary'][:100]}...")
                print(f"  Emotions: {list(result['emotion_distribution'].keys())}")
                break
            elif status == 'failed':
                print(f"  FAILED: {status_data.get('error')}")
                break

except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)
