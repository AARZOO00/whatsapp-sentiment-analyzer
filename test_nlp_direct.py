#!/usr/bin/env python3
"""Quick test of nlp_service directly."""
import sys
sys.path.insert(0, 'c:\\Users\\Aarzoo\\whatsapp-sentiment-analyzer\\backend')

from backend.services.nlp_service import nlp_service

sample = '''8/15/2024, 10:30 PM - Alice: Hey everyone! This is awesome!
8/15/2024, 10:31 PM - Bob: I'm doing great, thanks for asking!
8/15/2024, 10:32 PM - Charlie: Same here! This is wonderful!'''

print("Testing NLP Service directly...")
import time
start = time.time()
result = nlp_service.analyze_chat(sample)
elapsed = time.time() - start

print(f"Time: {elapsed:.2f}s")
print(f"Total messages: {result.get('total_messages')}")
print(f"Overall sentiment: {result.get('overall_sentiment')}")
print(f"Summary: {result.get('summary')[:100]}")
if 'error' in result:
    print(f"Error: {result['error']}")
