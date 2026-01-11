# 🚀 QUICK START GUIDE

## Get Up and Running in 5 Minutes

### Prerequisites
- Python 3.13+
- Node.js 18+
- npm or yarn

---

## Option 1: Development Mode (Recommended for Testing)

### Step 1: Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
✅ Backend runs at: **http://127.0.0.1:8000**

### Step 2: Start Frontend (New Terminal)
```bash
cd frontend
npm install
npm run dev
```
✅ Frontend runs at: **http://localhost:5174**

### Step 3: Test with Sample Chat
1. Open http://localhost:5174 in browser
2. Drag & drop `sample_chat.txt` into upload area
3. Wait for analysis (~2-5 seconds)
4. View results in dashboard

---

## Option 2: Docker (Production-like)

### One Command to Start Everything
```bash
docker-compose up --build
```

✅ Frontend: **http://localhost:80**
✅ Backend: **http://localhost:8000**

---

## Common Tasks

### Run Integration Tests
```bash
python test_integration.py
```
Expected: **ALL TESTS PASSED ✅**

### Build Frontend for Production
```bash
cd frontend
npm run build
```
Output: **dist/** folder (ready to deploy)

### View API Documentation
```
http://127.0.0.1:8000/docs
```

### Export Analysis Results
1. Upload chat file
2. View results
3. Click "📥 Export to CSV"
4. Download CSV with all analysis data

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Change to port 8001: `uvicorn main:app --port 8001` |
| Port 5174 in use | Vite auto-selects next port (check console) |
| Import error | Reinstall: `pip install -r requirements.txt` |
| Cannot connect | Ensure backend running on http://127.0.0.1:8000 |

---

## File Upload

### Supported Format
```
Date, Time - Sender: Message
8/15/2024, 10:30 PM - Alice: Hey everyone!
8/15/2024, 10:31 PM - Bob: Hi! I'm doing great!
```

### Maximum Size
- Up to 10,000 messages (~5-10 seconds to analyze)
- File size: typically < 10 MB

### What Gets Analyzed
- ✅ Sentiment (Positive/Negative/Neutral)
- ✅ Language (40+ languages)
- ✅ Emotions (Joy, Anger, Sadness, Fear, Surprise)
- ✅ Keywords (Most important words)
- ✅ Emojis (All emojis used)
- ✅ Users (Who participated)
- ✅ Activity (Message counts)

---

## API Usage

### Upload and Analyze
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "accept: application/json" \
  -F "file=@your_chat.txt"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Get Results (Poll)
```bash
curl -X GET "http://127.0.0.1:8000/results/550e8400-e29b-41d4-a716-446655440000"
```

Status: `processing` or `complete`

---

## Next Steps

1. ✅ **Try it out** - Upload sample chat
2. 📖 **Read docs** - See README_ENTERPRISE.md
3. 🎨 **Customize** - Modify colors, thresholds
4. 🚀 **Deploy** - Use docker-compose for production
5. 📈 **Scale** - Add database, API keys, etc.

---

## Features You Have

- 🌍 Multi-language support (40+ languages)
- 😊 Emotion detection
- 📊 Beautiful charts and visualizations
- 💾 CSV export
- 🎨 Professional UI with animations
- 📱 Responsive mobile design
- 🔄 Real-time analysis
- 🐳 Docker ready

---

## File Locations

```
whatsapp-sentiment-analyzer/
├── backend/           ← Python code
├── frontend/          ← React code
├── sample_chat.txt    ← Test data
├── docker-compose.yml ← Deploy with Docker
└── COMPLETION_SUMMARY.md ← Full details
```

---

## Performance

| Chat Size | Time | Memory |
|-----------|------|--------|
| 10 messages | ~0.5s | 200MB |
| 100 messages | ~1s | 220MB |
| 1000 messages | ~5s | 300MB |

---

## Support

### For Issues
1. Check DEPLOYMENT.md troubleshooting section
2. Review integration test output
3. Check browser dev console

### For Details
1. README_ENTERPRISE.md - Complete documentation
2. DEPLOYMENT.md - Deployment guide
3. Code comments - Implementation details

---

## Key Commands

```bash
# Start development
npm run dev          # Frontend dev server
uvicorn main:app --reload  # Backend dev server

# Production
npm run build        # Build frontend
docker-compose up    # Start with Docker

# Testing
python test_integration.py  # Run tests
npm run test         # Frontend tests

# Cleanup
docker-compose down  # Stop Docker
rm -rf node_modules  # Clean npm cache
rm -rf .venv         # Clean Python venv
```

---

## Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5174
- [ ] Can see "Chat Analytics Hub" on http://localhost:5174
- [ ] Can upload sample_chat.txt
- [ ] Results display in dashboard
- [ ] Charts render properly
- [ ] CSV export works

✅ **All checked? You're ready to go!**

---

Happy analyzing! 🎉

For more information, see:
- **COMPLETION_SUMMARY.md** - What's been built
- **README_ENTERPRISE.md** - Full API reference
- **DEPLOYMENT.md** - Deployment guide
