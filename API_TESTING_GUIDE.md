# 🧪 Complete API Testing Guide

## ✅ Backend Status

**Status**: ✅ Running on http://127.0.0.1:8000  
**Swagger UI**: http://127.0.0.1:8000/docs  

---

## 📋 All Available Endpoints

### Phase 1-2: Core Analytics (Working ✅)
| Endpoint | Method | Status | Test |
|----------|--------|--------|------|
| `/analyze` | POST | ✅ | Upload .txt file |
| `/results/{job_id}` | GET | ✅ | Poll with job_id |
| `/messages` | GET | ✅ | Query messages |
| `/stats` | GET | ✅ | Get statistics |

### Phase 3: Summarization (Ready 🆕)
| Endpoint | Method | Status |
|----------|--------|--------|
| `/summarize/{job_id}` | POST | ✅ Implemented |

### Phase 4: Multilingual (Ready 🆕)
| Endpoint | Method | Status |
|----------|--------|--------|
| `/translate` | POST | ✅ Implemented |
| `/language-stats/{job_id}` | GET | ✅ Implemented |

### Phase 5: Explainability (Ready 🆕)
| Endpoint | Method | Status |
|----------|--------|--------|
| `/explain/{message_id}` | GET | ✅ Implemented |
| `/disagreements/{job_id}` | GET | ✅ Implemented |

---

## 🧪 Testing Each Phase

### ✅ Phase 1-2: Test Message Filtering

#### Test 1: Get All Messages
```bash
curl "http://127.0.0.1:8000/messages?limit=10&page=1"
```

**Expected Response**:
```json
{
  "messages": [
    {
      "id": "...",
      "timestamp": "2024-01-15 10:30",
      "sender": "Alice",
      "text": "Hello everyone!",
      "language": "en",
      "ensemble_score": 0.85,
      "ensemble_label": "Positive",
      "emotions": {"joy": 0.8, "surprise": 0.2},
      "keywords": ["hello", "everyone"]
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 10,
  "total_pages": 15
}
```

#### Test 2: Filter by Sentiment
```bash
curl "http://127.0.0.1:8000/messages?sentiment=Positive&limit=50&page=1"
```

#### Test 3: Filter by User
```bash
curl "http://127.0.0.1:8000/messages?user=Alice&limit=50&page=1"
```

#### Test 4: Filter by Keyword
```bash
curl "http://127.0.0.1:8000/messages?keyword=hello&limit=50&page=1"
```

#### Test 5: Filter by Date Range
```bash
curl "http://127.0.0.1:8000/messages?start_date=2024-01-01&end_date=2024-01-31&limit=50&page=1"
```

#### Test 6: Get Statistics
```bash
curl "http://127.0.0.1:8000/stats"
```

**Expected Response**:
```json
{
  "total_messages": 150,
  "sentiment_distribution": {
    "Positive": 85,
    "Negative": 45,
    "Neutral": 20
  },
  "language_distribution": {
    "en": 120,
    "hi": 30
  },
  "top_participants": [
    {"name": "Alice", "count": 45},
    {"name": "Bob", "count": 35},
    {"name": "Charlie", "count": 20}
  ],
  "average_sentiment_score": 0.42
}
```

---

### 🆕 Phase 3: Test Summarization

#### Step 1: Upload and Analyze Chat
```bash
curl -X POST -F "file=@sample_chat.txt" http://127.0.0.1:8000/analyze
```

**Response**:
```json
{
  "job_id": "abc123-def456-ghi789"
}
```

#### Step 2: Poll for Completion
```bash
curl "http://127.0.0.1:8000/results/abc123-def456-ghi789"
```

**Response** (when complete):
```json
{
  "status": "complete",
  "result": {
    "messages": [...],
    "summary": "...",
    "total_messages": 150
  }
}
```

#### Step 3: Get Summarization
```bash
curl -X POST "http://127.0.0.1:8000/summarize/abc123-def456-ghi789"
```

**Expected Response**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "message_count": 150,
  "analysis": {
    "timestamp": "2025-01-11T10:30:00",
    "short_summary": "A lively discussion about weekend plans with mostly positive sentiment.",
    "detailed_summary": "The group had an engaging conversation about weekend activities. Alice suggested hiking, Bob proposed a movie night, and Charlie mentioned a dinner party. The overall tone was enthusiastic and supportive with some friendly disagreements about timing.",
    "key_topics": ["hiking", "movies", "dinner", "weekend"],
    "emotional_trend": {
      "windows": [
        {
          "window": 1,
          "messages_count": 50,
          "positive": 40,
          "negative": 5,
          "trend": "positive"
        },
        {
          "window": 2,
          "messages_count": 50,
          "positive": 35,
          "negative": 10,
          "trend": "positive"
        },
        {
          "window": 3,
          "messages_count": 50,
          "positive": 45,
          "negative": 3,
          "trend": "positive"
        }
      ],
      "overall_trend": "improving"
    }
  }
}
```

---

### 🆕 Phase 4: Test Multilingual

#### Test 1: Translate Text to Spanish
```bash
curl -X POST "http://127.0.0.1:8000/translate?text=Hello%20how%20are%20you&target_language=es"
```

**Expected Response**:
```json
{
  "original_text": "Hello how are you",
  "translated_text": "Hola, ¿cómo estás?",
  "source_language": "English",
  "source_language_code": "en",
  "target_language": "Spanish",
  "target_language_code": "es",
  "detection_confidence": 0.99,
  "is_hinglish": false,
  "hinglish_analysis": null
}
```

#### Test 2: Detect Hinglish
```bash
curl -X POST "http://127.0.0.1:8000/translate?text=Haan%20bhai%20theek%20hai%20awesome&target_language=en"
```

**Expected Response** (Hinglish detected):
```json
{
  "original_text": "Haan bhai theek hai awesome",
  "translated_text": "Yes brother okay fine awesome",
  "source_language": "Hindi",
  "source_language_code": "hi",
  "target_language": "English",
  "target_language_code": "en",
  "detection_confidence": 0.85,
  "is_hinglish": true,
  "hinglish_analysis": {
    "positive_indicators": ["awesome"],
    "negative_indicators": [],
    "neutral_indicators": ["theek hai", "haan"],
    "hinglish_confidence": 0.8
  }
}
```

#### Test 3: Get Language Statistics
```bash
curl "http://127.0.0.1:8000/language-stats/abc123-def456-ghi789"
```

**Expected Response**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "language_statistics": {
    "total_messages": 150,
    "language_distribution": {
      "en": 100,
      "hi": 40,
      "es": 10
    },
    "hinglish_messages": 12,
    "primary_language": "en",
    "language_diversity": 3
  }
}
```

---

### 🆕 Phase 5: Test Explainability

#### Test 1: Get Message Explanation
```bash
curl "http://127.0.0.1:8000/explain/message_id_123"
```

**Expected Response**:
```json
{
  "message_id": "message_id_123",
  "text_preview": "I absolutely love this! It's amazing!",
  "per_model_analysis": {
    "vader": {
      "score": 0.87,
      "confidence": 0.95,
      "label": "Positive",
      "explanation": "VADER strongly detects positive sentiment (0.87). Uses lexicon-based approach with emphasis on positive words like 'love' and 'amazing'."
    },
    "textblob": {
      "score": 0.85,
      "confidence": 0.92,
      "label": "Positive",
      "explanation": "TextBlob strongly detects positive sentiment (0.85). Uses subjectivity and polarity analysis on word levels."
    },
    "ensemble": {
      "score": 0.86,
      "confidence": 0.94,
      "label": "Positive",
      "explanation": "Weighted combination of VADER (60%) and TextBlob (40%)"
    }
  },
  "disagreement": null,
  "confidence_metrics": {
    "model_agreement_score": 0.98,
    "overall_confidence_level": "high",
    "vader_confidence": 0.95,
    "textblob_confidence": 0.92,
    "ensemble_confidence": 0.94,
    "recommendation": "High confidence - reliable sentiment classification"
  },
  "important_words": {
    "positive_indicators": ["love", "amazing"],
    "negative_indicators": []
  },
  "final_verdict": {
    "sentiment": "Positive",
    "score": 0.86,
    "confidence": 0.94
  }
}
```

#### Test 2: Find Model Disagreements
```bash
curl "http://127.0.0.1:8000/disagreements/abc123-def456-ghi789"
```

**Expected Response**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "total_messages": 150,
  "disagreement_count": 8,
  "disagreement_rate": "5.3%",
  "disagreements": [
    {
      "message": "I guess it's okay, could be better though",
      "sender": "Alice",
      "timestamp": "2024-01-15 14:30",
      "disagreement_info": {
        "disagreement": true,
        "vader_says": "Positive",
        "textblob_says": "Negative",
        "possible_reason": "Text likely has subtle sentiment indicators that differ in interpretation. VADER sees 'okay' positively, TextBlob focuses on 'could be better'.",
        "recommendation": "Manual review recommended for this message"
      }
    }
  ]
}
```

---

## 🧪 Using cURL for Testing

### Basic Pattern
```bash
# Simple GET
curl "http://127.0.0.1:8000/endpoint"

# GET with query parameters
curl "http://127.0.0.1:8000/endpoint?param1=value1&param2=value2"

# POST with data
curl -X POST "http://127.0.0.1:8000/endpoint?param=value"

# POST with file upload
curl -X POST -F "file=@path/to/file.txt" http://127.0.0.1:8000/endpoint
```

### Pretty Print JSON
```bash
# Using Python (built-in)
curl "http://127.0.0.1:8000/messages?limit=5" | python -m json.tool

# Using jq (if installed)
curl "http://127.0.0.1:8000/messages?limit=5" | jq
```

---

## 🌐 Using Swagger UI

Open in browser:
```
http://127.0.0.1:8000/docs
```

Features:
- See all endpoints
- Try endpoints directly
- View request/response schemas
- See parameter descriptions

---

## 🔍 Testing Workflow

### Complete End-to-End Test

#### 1. Upload Chat (1-2 seconds)
```bash
curl -X POST -F "file=@sample_chat.txt" http://127.0.0.1:8000/analyze
# Get job_id from response
```

#### 2. Poll Results (15-20 seconds first time)
```bash
# Keep polling until status = "complete"
curl "http://127.0.0.1:8000/results/{job_id}"
```

#### 3. Test Filtering (once messages are stored)
```bash
curl "http://127.0.0.1:8000/messages?limit=10&page=1"
curl "http://127.0.0.1:8000/messages?user=Alice&sentiment=Positive"
curl "http://127.0.0.1:8000/stats"
```

#### 4. Test Summarization
```bash
curl -X POST "http://127.0.0.1:8000/summarize/{job_id}"
```

#### 5. Test Explainability
```bash
# Get a message_id from /messages response, then:
curl "http://127.0.0.1:8000/explain/{message_id}"
curl "http://127.0.0.1:8000/disagreements/{job_id}"
```

#### 6. Test Translation
```bash
curl -X POST "http://127.0.0.1:8000/translate?text=Hello&target_language=es"
```

---

## 📊 Response Time Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Upload & Analyze (first) | 15-20s | Loads transformer models |
| Upload & Analyze (cached) | 2-5s | Models already loaded |
| Get Messages (with filters) | <500ms | SQLite with indices |
| Get Statistics | <500ms | Aggregation query |
| Summarization | 3-5s | BART model inference |
| Translation | 1-2s | API call to Google |
| Message Explanation | <100ms | Database lookup |
| Find Disagreements | 2-3s | Processing all messages |

---

## ❌ Common Errors & Solutions

### Error: Port 8000 Already in Use
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error: Job Not Found
- Ensure job_id is correct
- Wait for analysis to complete (status = "complete")
- Check backend logs for errors

### Error: Message Not Found
- Ensure analysis completed
- Make sure message_id is from `/messages` endpoint
- Try `/messages` endpoint to list all IDs

### Error: Model Disagreements Empty
- Not all messages will have disagreements
- Try multiple job_ids to find one with disagreements
- Disagreements are rare (typically 5-10% of messages)

---

## 🎯 Test Checklist

- [ ] Backend running at http://127.0.0.1:8000
- [ ] Swagger UI accessible at /docs
- [ ] Can upload chat file
- [ ] Analysis completes and returns job_id
- [ ] Can poll results
- [ ] Messages stored in database
- [ ] Can filter messages by sentiment
- [ ] Can filter by user
- [ ] Can search by keyword
- [ ] Stats endpoint returns data
- [ ] Can get summarization
- [ ] Can translate text
- [ ] Can explain messages
- [ ] Can find disagreements

---

## 📞 Support Commands

### Check Backend Health
```bash
curl http://127.0.0.1:8000/docs
# Should load Swagger UI
```

### View All Messages
```bash
curl "http://127.0.0.1:8000/messages?limit=100&page=1"
```

### Clear Database
```bash
# Delete and restart backend
rm backend/analyzer.db
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### View Backend Logs
```bash
# Logs printed to terminal where backend is running
# Look for INFO, WARNING, or ERROR messages
```

---

## ✅ You're Ready to Test!

All endpoints are implemented and ready for testing. Use this guide to verify each phase is working correctly.

**Happy testing!** 🚀
