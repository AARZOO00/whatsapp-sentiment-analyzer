# How to Run & Test the Upgraded Platform

## 🎯 What You Now Have

A **professional AI analytics platform** with:
- ✅ Phase 1: Backend message filtering APIs with SQLite persistence
- ✅ Phase 2: Interactive Chat Viewer UI with advanced filters
- ⏳ Phases 3-6: Ready for implementation

---

## 🚀 Quick Start (5 Minutes)

### Terminal 1: Start Backend
```bash
cd c:\Users\Aarzoo\whatsapp-sentiment-analyzer
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --lifespan off
```

**Expected Output:**
```
INFO:backend.database:Database initialized successfully
INFO:backend.services.nlp_service:✓ NLP Service initialized
INFO:     Started server process [XXXX]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Start Frontend
```bash
cd c:\Users\Aarzoo\whatsapp-sentiment-analyzer\frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

### Browser: Visit the App
```
http://localhost:5173/
```

---

## 📊 Usage Flow

### 1. Upload & Analyze (Analysis Tab)
- Click **📊 Analysis** tab
- Drag & drop or select `sample_chat.txt`
- Wait ~15-20 seconds for analysis
- View results: sentiment, emotions, top users, summary

### 2. Explore Messages (Chat Explorer Tab)
- Click **💬 Chat Explorer** tab
- See all analyzed messages in a paginated table
- **Filters available:**
  - 📅 Date range (start_date, end_date)
  - 👤 Participant (dropdown of all speakers)
  - 😊 Sentiment (Positive / Negative / Neutral)
  - 🔍 Keyword (text search)
- Click **Apply Filters** to see filtered results
- Click **View** on any row to see message details in modal
- Use **Previous/Next** to navigate pages

---

## 🧪 Test the APIs Directly

### Test 1: Backend Health
```bash
curl http://127.0.0.1:8000/docs
```
Should return 200 with Swagger UI

### Test 2: Upload & Analyze
```bash
curl -X POST -F "file=@sample_chat.txt" http://127.0.0.1:8000/analyze
```
Returns:
```json
{
  "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Test 3: Poll Results
```bash
curl http://127.0.0.1:8000/results/{job_id}
```
Returns:
```json
{
  "status": "complete",
  "result": { ...analysis results... }
}
```

### Test 4: Get All Messages
```bash
curl "http://127.0.0.1:8000/messages?limit=50&page=1"
```
Returns paginated messages array

### Test 5: Filter by User
```bash
curl "http://127.0.0.1:8000/messages?user=Alice&limit=50&page=1"
```
Returns only Alice's messages

### Test 6: Filter by Sentiment
```bash
curl "http://127.0.0.1:8000/messages?sentiment=Positive&limit=50&page=1"
```
Returns only positive messages

### Test 7: Get Statistics
```bash
curl "http://127.0.0.1:8000/stats"
```
Returns sentiment distribution, top users, language stats, average score

---

## 🧪 Run Test Suites

### Database Unit Tests
```bash
python test_database_direct.py
```
Expected: All database operations pass ✓

### Quick Integration Test
```bash
python test_phase1_quick.py
```
Expected: Analysis complete, filters working ✓

### API Client Test
```bash
python test_api_client.py
```
Expected: Upload, analyze, poll results ✓

---

## 📁 Key Files & Structure

### Backend
```
backend/
├── main.py                  # FastAPI app with /analyze, /results, /messages, /stats
├── database.py              # SQLite models & filtering logic
├── schemas.py               # Pydantic schemas
├── services/
│   ├── nlp_service.py      # Chat parsing, sentiment analysis
│   ├── sentiment.py        # VADER + TextBlob + Transformers
│   └── language.py         # Language detection + translation
└── analyzer.db             # SQLite database (auto-created)
```

### Frontend
```
frontend/src/
├── App.tsx                  # Main app with tab navigation
├── components/
│   ├── ChatViewer.tsx      # Message explorer (NEW - Phase 2)
│   ├── ChatViewer.css      # Styling for explorer (NEW - Phase 2)
│   ├── Dashboard.tsx       # Analysis results display
│   └── FileUpload.tsx      # Chat file uploader
└── api.ts                  # API integration
```

### Documentation
```
PHASE1_API_DOCS.md         # Complete backend API reference
PHASE2_CHAT_VIEWER.md      # Frontend component documentation
UPGRADE_SUMMARY.md         # Overview of all changes
QUICK_TEST_GUIDE.md        # This file (you are here)
```

---

## 🔍 What Each Endpoint Does

| Endpoint | Method | Purpose | New? |
|----------|--------|---------|------|
| `/analyze` | POST | Upload chat file, start analysis | Existing |
| `/results/{job_id}` | GET | Poll for analysis results | Existing |
| `/messages` | GET | Query messages with filters | ✨ **NEW Phase 1** |
| `/stats` | GET | Get aggregated statistics | ✨ **NEW Phase 1** |

---

## 💾 Database Schema (SQLite)

### messages table (NEW - Phase 1)
```sql
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  timestamp DATETIME,
  sender TEXT,
  text TEXT,
  translated_text TEXT,
  language TEXT,
  vader_score REAL,
  textblob_score REAL,
  ensemble_score REAL,
  ensemble_label TEXT,
  emotions JSON,
  keywords JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexed on: sender, timestamp, sentiment, language, job_id
```

All messages from uploaded chats are automatically stored here!

---

## 🎨 Chat Explorer Features (Phase 2)

### Statistics Dashboard
- Total message count
- Average sentiment score
- Top participant (most active)
- Auto-updates with filters

### Message Table
- Paginated display (25 per page)
- Columns: Timestamp | Sender | Message | Sentiment | Language | Score | View
- Sentiment badges (color-coded)
- Hoverable rows

### Advanced Filters
1. **Date Range**: Start date, end date
2. **Participant**: Dropdown (auto-populated)
3. **Sentiment**: Positive / Negative / Neutral
4. **Keyword**: Text search
5. **Apply**: Apply all filters together
6. **Reset**: Clear all filters

### Message Detail Modal
- Full message text
- Translated text (if available)
- Sentiment score & label
- Language detected
- Emotions breakdown (joy, anger, sadness, fear, surprise)
- Keywords extracted

### Pagination
- Previous / Next buttons
- Page indicator (Page X of Y)
- Dynamic calculation of total pages

### Responsive Design
- Works on desktop, tablet, mobile
- Dark mode support
- Professional color scheme

---

## 🐛 Troubleshooting

### Issue: Port 8000 Already in Use
```bash
# Kill the process
lsof -ti:8000 | xargs kill -9
# Or on Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: Database Locked
```bash
# Remove old database and restart
rm backend/analyzer.db
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --lifespan off
```

### Issue: CORS Error in Frontend
- Ensure backend is running on `http://127.0.0.1:8000`
- Check `frontend/src/components/ChatViewer.tsx` has correct `API_BASE`

### Issue: Analysis Slow
- First run loads transformer models (~15s)
- Subsequent runs faster (~2-5s)
- Don't close backend during analysis

### Issue: No Messages Appearing in Chat Explorer
1. Make sure you uploaded a chat in the Analysis tab first
2. Wait for analysis to complete (check status)
3. The database is populated after analysis completes
4. Refresh Chat Explorer tab

---

## ✅ Validation Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads (http://localhost:5173)
- [ ] Can upload chat file
- [ ] Analysis completes and shows results
- [ ] Chat Explorer tab loads
- [ ] Messages appear in table
- [ ] Can filter by user
- [ ] Can filter by sentiment
- [ ] Can search keyword
- [ ] Can navigate pages
- [ ] Can open message detail modal
- [ ] Mobile view works (try responsive design mode)

---

## 📈 What's New in This Upgrade

| Feature | Location | Type |
|---------|----------|------|
| SQLite persistence | `backend/database.py` | NEW Phase 1 |
| `/messages` endpoint | `backend/main.py` | NEW Phase 1 |
| `/stats` endpoint | `backend/main.py` | NEW Phase 1 |
| Advanced filtering | `backend/database.py` | NEW Phase 1 |
| Chat Viewer component | `frontend/src/components/ChatViewer.tsx` | NEW Phase 2 |
| Professional styling | `frontend/src/components/ChatViewer.css` | NEW Phase 2 |
| Tab navigation | `frontend/src/App.tsx` | UPDATED Phase 2 |

---

## 🎯 Next Steps

### To Proceed with Phase 3 (Summarization):
- Detailed conversation summaries
- Key topics extraction
- Emotional trend analysis
- Caching for performance

### To Proceed with Phase 4 (Multilingual):
- Better language detection
- Auto-translation
- Multilingual sentiment models
- Support: Hindi, Hinglish, Urdu, Spanish, French

### To Proceed with Phase 5 (Explainable AI):
- Per-model sentiment breakdown
- Word-level importance
- Confidence metrics
- Disagreement explanations

### To Proceed with Phase 6 (UI Polish):
- Loading skeletons
- Empty state designs
- Mobile optimization
- Dark mode refinement

---

## 📚 Read More

For detailed information:
- **Backend API**: See `PHASE1_API_DOCS.md`
- **Frontend Component**: See `PHASE2_CHAT_VIEWER.md`
- **Complete Overview**: See `UPGRADE_SUMMARY.md`

---

## 🎉 You're Ready!

Your professional WhatsApp Sentiment Analyzer is fully functional.

**Enjoy your new Chat Explorer! 💬✨**
