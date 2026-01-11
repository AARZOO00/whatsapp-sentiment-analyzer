# Quick Test Guide

## 🚀 Running the Full Application

### Quick Start (2 minutes)

#### Step 1: Terminal 1 - Start Backend
```bash
cd c:\Users\Aarzoo\whatsapp-sentiment-analyzer\backend
python -m uvicorn main:app --reload
```

Expected Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
INFO:     NLP Service initialized
```

#### Step 2: Terminal 2 - Start Frontend
```bash
cd c:\Users\Aarzoo\whatsapp-sentiment-analyzer\frontend
npm run dev
```

Expected Output:
```
VITE v7.3.1 ready in XXX ms
Local:   http://localhost:5173/
```

#### Step 3: Open Browser
- Navigate to: **http://localhost:5173/**
- You should see the water/shine themed dashboard

#### Step 4: Upload Sample Chat
1. Download `sample_chat.txt` (it's in the root directory)
2. Drag and drop it onto the upload area
3. Click "Start Analysis"
4. Wait 1-2 seconds for results
5. View the dashboard with 4 charts

---

## 🧪 Testing Without Browser

### Test 1: Check Backend is Running
```powershell
curl http://127.0.0.1:8000/docs
```
Should return HTML documentation page (HTTP 200)

### Test 2: Upload and Analyze (Quick Test)
```powershell
$file = "c:\Users\Aarzoo\whatsapp-sentiment-analyzer\sample_chat.txt"
$form = @{
    file = @{
        Path = $file
    }
}
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/analyze" -Method Post -Form $form
$jobId = ($response.Content | ConvertFrom-Json).job_id
Write-Host "Job ID: $jobId"
```

### Test 3: Get Results
```powershell
$jobId = "your-job-id-here"
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/results/$jobId"
Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json)
```

---

## 📊 What to Expect in Results

### Overall Structure
```json
{
  "status": "complete",
  "result": {
    "total_messages": 7,
    "overall_sentiment": {
      "ensemble_score": 0.206,
      "ensemble_label": "Positive",
      "vader_score": 0.206
    },
    "language_distribution": {
      "en": 100.0
    },
    "primary_language": "en",
    "emotion_distribution": {
      "joy": 2.1,
      "anger": 0.3,
      "sadness": 0.5,
      "fear": 0.1,
      "surprise": 0.8
    },
    "most_active_users": [
      ["Alice", 3],
      ["Bob", 2],
      ["Charlie", 2]
    ],
    "top_emojis": [],
    "messages": [
      {
        "datetime": "8/15/2024, 10:30 PM",
        "sender": "Alice",
        "message": "Hey everyone! How's everyone doing?",
        "language": "en",
        "sentiment": {
          "vader_score": 0.0,
          "vader_label": "Neutral",
          "textblob_score": 0.0,
          "ensemble_score": 0.0,
          "ensemble_label": "Neutral",
          "confidence": 0.0
        },
        "emotions": {
          "joy": 0.3,
          "anger": 0.0,
          "sadness": 0.0,
          "fear": 0.0,
          "surprise": 0.1
        },
        "keywords": ["everyone"],
        "emojis": []
      }
    ],
    "summary": "Analyzed 7 messages with Positive overall sentiment"
  }
}
```

---

## 🎨 Dashboard Features to Test

### 1. File Upload Section
- [ ] Drag and drop file
- [ ] Select file via dialog
- [ ] Show loading spinner
- [ ] Display success/error message

### 2. KPI Cards (Top)
- [ ] Total Messages count
- [ ] Overall Sentiment label and score
- [ ] Primary Language
- [ ] Top User names

### 3. User Activity Chart (Bottom Left)
- [ ] Bar chart showing message count per user
- [ ] Teal (#00bcd4) colored bars
- [ ] Proper axis labels
- [ ] Responsive sizing

### 4. Emotion Distribution (Bottom Middle)
- [ ] Donut chart with 5 emotions
- [ ] Color-coded by emotion
- [ ] Proper percentages
- [ ] Legend shows

### 5. Language Distribution (Bottom Right)
- [ ] Pie chart showing language percentages
- [ ] Teal color palette
- [ ] Language codes displayed
- [ ] Percentages visible

### 6. Export Button
- [ ] Click "Export CSV"
- [ ] File downloads as CSV
- [ ] Open in Excel/Google Sheets
- [ ] All data preserved

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr ":8000"

# Kill existing process if needed
taskkill /PID <PID> /F

# Make sure you're in backend folder
cd backend

# Try starting again
python -m uvicorn main:app --reload
```

### Frontend won't start
```bash
# Make sure Node is installed
node --version

# Make sure npm is installed
npm --version

# Install dependencies if needed
npm install

# Try starting again
npm run dev
```

### API not responding
```bash
# Check if backend is running
curl http://127.0.0.1:8000/docs

# Check console for errors
# Look at backend terminal for log messages
# Restart both services
```

### Analysis fails
```bash
# Check file format (must be .txt)
# Check file encoding (must be UTF-8)
# Check backend logs for error details
# Try with sample_chat.txt first
```

---

## 📈 Sample Data for Testing

### Create a test chat file
```
8/15/2024, 10:30 PM - Alice: Hey everyone! How's everyone doing?
8/15/2024, 10:31 PM - Bob: Hi! I'm doing great, thanks for asking!
8/15/2024, 10:32 PM - Charlie: Same here! This is awesome!
8/15/2024, 10:33 PM - Alice: That's wonderful! I'm so happy to hear that!
8/15/2024, 10:34 PM - Bob: Unfortunately I had a bad day at work though
8/15/2024, 10:35 PM - Charlie: Oh no, what happened? That's terrible!
8/15/2024, 10:36 PM - Alice: Hope things get better soon!
```

---

## ✅ Final Verification

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Dashboard displays correctly
- [ ] File upload works
- [ ] Analysis completes in < 2 seconds
- [ ] Results display in dashboard
- [ ] All 4 charts render
- [ ] Data looks reasonable
- [ ] Export CSV works
- [ ] No console errors
- [ ] No API errors
- [ ] Theme colors are correct (teal/cyan)

**If all checkmarks above are complete, the system is working perfectly!** ✅

---

## 🎯 Success Indicators

### Backend
- ✅ Server starts and listens on 127.0.0.1:8000
- ✅ OpenAPI docs available at /docs
- ✅ Accepts file uploads on /analyze endpoint
- ✅ Returns job IDs
- ✅ Processes in background
- ✅ Results available via /results/{job_id}

### Frontend
- ✅ Dashboard loads at localhost:5173
- ✅ Water/shine theme visible
- ✅ Upload area visible
- ✅ Charts render after analysis
- ✅ CSV export works
- ✅ No TypeScript errors
- ✅ No React console errors

### Integration
- ✅ Frontend can reach backend API
- ✅ File uploads complete successfully
- ✅ Analysis results return as expected
- ✅ Data displays correctly on dashboard
- ✅ All features work as designed

---

**Everything working?** Great! Your WhatsApp Sentiment Analyzer is ready to use! 🚀
