# Phase 1: Backend Message Storage & Filtering APIs

## Overview

Phase 1 implements a professional backend filtering system using SQLite for persistent message storage, with RESTful APIs for querying, filtering, and analyzing messages.

---

## Architecture

### Database Schema

SQLite tables:

- **messages**: Stores parsed messages with full sentiment analysis
  - id (TEXT PRIMARY KEY)
  - job_id (TEXT)
  - timestamp (DATETIME)
  - sender (TEXT)
  - text (TEXT)
  - translated_text (TEXT, optional)
  - language (TEXT)
  - vader_score, textblob_score, ensemble_score (REAL)
  - ensemble_label (TEXT: Positive/Negative/Neutral)
  - emotions (JSON)
  - keywords (JSON)
  - Indexed on: sender, timestamp, sentiment, language, job_id

- **summaries**: Conversation summaries per job
- **jobs**: Analysis job metadata

---

## API Endpoints

### 1. GET /messages

**Retrieve messages with advanced filtering and pagination.**

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_date` | string (optional) | Filter by start date (ISO format) | `2024-01-15` |
| `end_date` | string (optional) | Filter by end date (ISO format) | `2024-01-20` |
| `user` | string (optional) | Filter by sender name (exact match) | `Alice` |
| `keyword` | string (optional) | Search keyword in message text | `awesome` |
| `sentiment` | string (optional) | Filter by sentiment label | `Positive` \| `Negative` \| `Neutral` |
| `language` | string (optional) | Filter by detected language code | `en` \| `hi` \| `es` |
| `limit` | integer | Messages per page (1-500, default 50) | `25` |
| `page` | integer | Page number (1-indexed, default 1) | `2` |

#### Response (200 OK)

```json
{
  "messages": [
    {
      "id": "job_uuid_timestamp_sender",
      "timestamp": "2024-08-15 10:30:00",
      "sender": "Alice",
      "text": "Hey everyone! This is awesome!",
      "translated_text": null,
      "language": "en",
      "vader_score": 0.775,
      "textblob_score": 0.800,
      "ensemble_score": 0.775,
      "ensemble_label": "Positive",
      "emotions": {
        "joy": 0.95,
        "sadness": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "surprise": 0.05
      },
      "keywords": ["awesome", "everyone"]
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "total_pages": 3
}
```

#### Example Requests

**Get all messages (page 1, 50 per page):**
```
GET /messages?page=1&limit=50
```

**Get Alice's messages:**
```
GET /messages?user=Alice&limit=50&page=1
```

**Get positive messages:**
```
GET /messages?sentiment=Positive&limit=50&page=1
```

**Search for a keyword:**
```
GET /messages?keyword=problem&limit=50&page=1
```

**Date range + sentiment:**
```
GET /messages?start_date=2024-01-15&end_date=2024-01-20&sentiment=Negative&limit=50&page=1
```

**Filter by language:**
```
GET /messages?language=hi&limit=50&page=1
```

---

### 2. GET /stats

**Get aggregated statistics over filtered messages.**

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string (optional) | Filter by start date |
| `end_date` | string (optional) | Filter by end date |
| `user` | string (optional) | Filter by sender |

#### Response (200 OK)

```json
{
  "total_messages": 150,
  "sentiment_distribution": {
    "Positive": {
      "count": 85,
      "avg_score": 0.72
    },
    "Negative": {
      "count": 35,
      "avg_score": -0.68
    },
    "Neutral": {
      "count": 30,
      "avg_score": 0.02
    }
  },
  "language_distribution": {
    "en": 120,
    "hi": 20,
    "es": 10
  },
  "top_participants": {
    "Alice": 45,
    "Bob": 38,
    "Charlie": 35,
    "David": 20,
    "Eve": 12
  },
  "average_sentiment_score": 0.26
}
```

#### Example Requests

**Overall statistics:**
```
GET /stats
```

**Stats for a specific user:**
```
GET /stats?user=Alice
```

**Stats for a date range:**
```
GET /stats?start_date=2024-01-15&end_date=2024-01-20
```

---

## Error Handling

All errors return structured JSON responses:

```json
{
  "detail": "Invalid sentiment: BadValue. Must be Positive, Negative, or Neutral."
}
```

| Status Code | Scenario |
|-------------|----------|
| 400 | Invalid query parameter |
| 404 | Job not found |
| 500 | Server error |

---

## Filtering Logic

### AND Operations

Multiple filters are combined with AND logic:
```
/messages?user=Alice&sentiment=Positive&language=en
```
Returns messages where: sender="Alice" AND sentiment="Positive" AND language="en"

### LIKE Search

Keyword search uses SQL LIKE (substring matching):
```
/messages?keyword=error
```
Matches: "There was an error", "Error in code", etc.

### Date Range

ISO date format (YYYY-MM-DD):
```
/messages?start_date=2024-01-15&end_date=2024-01-20
```

---

## Pagination Details

- **Total Pages Formula**: `(total + limit - 1) // limit`
- **Offset Calculation**: `(page - 1) * limit`
- **Max Limit**: 500 messages per page
- **Default Limit**: 50 messages per page

Example: 150 total messages, 50 per page = 3 pages

---

## Database Performance

### Indices

- `idx_sender` on sender column (fast user filtering)
- `idx_timestamp` on timestamp column (fast date range queries)
- `idx_sentiment` on ensemble_label (fast sentiment filtering)
- `idx_language` on language column (fast language filtering)
- `idx_job` on job_id column (fast job lookup)

### Query Optimization

All filtering is done on the database (not in Python), ensuring:
- Fast queries on large datasets
- Minimal memory usage
- Proper index utilization

---

## Integration with Frontend

### Step 1: Get Overview Statistics

```javascript
const response = await fetch('/stats');
const stats = await response.json();
console.log(stats.total_messages);
console.log(stats.sentiment_distribution);
```

### Step 2: Fetch Messages with Filters

```javascript
const params = new URLSearchParams({
  user: 'Alice',
  sentiment: 'Positive',
  limit: 50,
  page: 1
});
const response = await fetch(`/messages?${params}`);
const data = await response.json();
console.log(data.messages);  // Array of 50 messages
console.log(data.total_pages);  // For pagination UI
```

### Step 3: Build UI Components

- Display `messages` array in a table
- Render pagination controls using `total_pages`
- Update filters and re-fetch on user interaction

---

## Testing

Run the database unit test:
```bash
python test_database_direct.py
```

Expected output:
```
Testing database functions directly...
✓ Database initialized
✓ 3 messages inserted
✓ Query all: 3 messages found
✓ Filter by sender (Alice): 2 messages
✓ Filter by sentiment (Positive): 2 messages
✓ Filter by sentiment (Negative): 1 messages
✓ Keyword search ('awesome'): 1 messages
✓ Stats computed: ...
DATABASE TESTS: ALL PASSED ✓
```

---

## Next Steps (Phase 2)

Build the Chat Viewer UI component:
- Paginated message table
- Interactive filters (date range picker, participant dropdown, sentiment badges)
- Search bar for keywords
- Message detail modal on row click
- Real-time filter updates via API

