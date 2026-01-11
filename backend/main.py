from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.services.nlp_service import nlp_service
from backend.schemas import AnalysisResult, ParsingError, PaginatedMessages, MessageDB, FilterStats
from backend.database import init_db, insert_message, query_messages, get_stats
from backend.services.summarization_service import get_summarization_service
from backend.services.multilingual_service import get_multilingual_service
from backend.services.explainable_ai_service import get_explainable_ai_service
from uuid import uuid4
import logging
import traceback
from typing import Any, Dict, Optional
import json
from datetime import datetime

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

app = FastAPI()

# --- Job Store ---
# In-memory store for job statuses and results.
# For production, a more robust solution like Redis would be used.
job_store = {}

# --- CORS ---
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_analysis_task(job_id: str, content: str):
    """The background task that runs the NLP analysis and stores results in database."""
    logger.info("Background task started for job %s", job_id)
    try:
        results = nlp_service.analyze_chat(content)
        
        # If analyze_chat returns an error payload, mark as failed with details
        if isinstance(results, dict) and results.get('error'):
            logger.error("Analysis returned error for job %s: %s", job_id, results.get('error'))
            job_store[job_id] = {"status": "failed", "error": results.get('error'), "detail": results}
            return
        
        # Store messages in database
        try:
            messages = results.get('messages', [])
            for msg in messages:
                msg_id = f"{job_id}_{msg.get('timestamp', '')}_{''.join(msg.get('sender', '').split())}"
                
                # Extract sentiment scores
                sentiment = msg.get('sentiment', {})
                emotions_json = json.dumps(msg.get('emotions', {}))
                keywords_list = [k[0] for k in msg.get('keywords', [])]  # Extract keyword names
                keywords_json = json.dumps(keywords_list)
                
                # Insert message into database
                insert_message(
                    msg_id=msg_id,
                    job_id=job_id,
                    timestamp=msg.get('timestamp', ''),
                    sender=msg.get('sender', ''),
                    text=msg.get('message', ''),
                    translated_text=msg.get('translated_message'),
                    language=msg.get('language', 'en'),
                    vader_score=sentiment.get('vader_score', 0.0),
                    textblob_score=sentiment.get('textblob_score', 0.0),
                    ensemble_score=sentiment.get('ensemble_score', 0.0),
                    ensemble_label=sentiment.get('ensemble_label', 'Neutral'),
                    emotions=emotions_json,
                    keywords=keywords_json,
                )
            logger.info(f"Stored {len(messages)} messages for job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to store messages in database: {e}")
            # Continue anyway - don't fail the analysis
        
        # Store result atomically
        job_store[job_id] = {"status": "complete", "result": results}
        logger.info("Background task complete for job %s", job_id)
        
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Analysis failed for job %s: %s", job_id, str(e))
        job_store[job_id] = {"status": "failed", "error": str(e), "traceback": tb}

@app.post("/analyze", status_code=202)
async def analyze_chat_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Accepts a chat file, starts a background analysis task, and returns a job ID.
    """
    # Validate filename
    if not file.filename or not file.filename.lower().endswith(".txt"):
        return {"error": "Only .txt files are allowed."}

    # Read and validate file content
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    if not file_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Decode with utf-8 with replacement to avoid UnicodeDecodeError
    try:
        chat_content = file_content.decode("utf-8")
    except Exception:
        try:
            chat_content = file_content.decode("utf-8", errors='replace')
            logger.warning("Uploaded file had encoding issues; decoded with replacement characters.")
        except Exception as e:
            logger.error("Failed to decode file: %s", e)
            raise HTTPException(status_code=400, detail="Failed to decode file. Ensure it's UTF-8 encoded.")

    # Basic content validation
    if len(chat_content.strip()) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file contains no readable text.")

    job_id = str(uuid4())
    job_store[job_id] = {"status": "processing"}

    # Run analysis in background with protected wrapper and log scheduling
    try:
        logger.info("Scheduling background analysis task for job %s", job_id)
        background_tasks.add_task(run_analysis_task, job_id, chat_content)
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Failed to schedule background task for job %s: %s", job_id, str(e))
        job_store[job_id] = {"status": "failed", "error": str(e), "traceback": tb}
        raise HTTPException(status_code=500, detail={"error": "Failed to start analysis task.", "detail": str(e)})

    return {"job_id": job_id}

@app.get("/results/{job_id}")
async def get_analysis_results(job_id: str):
    """
    Poll this endpoint with the job_id to get the analysis status and results.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error": "Job not found."})

    if job.get("status") == "processing":
        return {"status": "processing"}

    if job.get("status") == "failed":
        # Return structured error JSON rather than raising silent exceptions
        return {"status": "failed", "error": job.get("error"), "traceback": job.get("traceback"), "detail": job.get('detail')}

    # Return the final result
    analysis_result = job.get("result")
    if not analysis_result:
        return {"status": "failed", "error": "No result available for this job."}

    # If the analysis result contains an error payload, surface it
    if isinstance(analysis_result, dict) and analysis_result.get('error'):
        return {"status": "failed", "error": analysis_result.get('error'), "detail": analysis_result}

    return {"status": "complete", "result": analysis_result}


# ============================================================================
# PHASE 1: MESSAGE FILTERING AND ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/messages", response_model=PaginatedMessages)
async def get_messages(
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    user: Optional[str] = Query(None, description="Filter by sender name"),
    keyword: Optional[str] = Query(None, description="Search keyword in message text"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (Positive/Negative/Neutral)"),
    language: Optional[str] = Query(None, description="Filter by detected language (en, hi, etc.)"),
    limit: int = Query(50, ge=1, le=500, description="Number of messages per page"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
):
    """
    Retrieve messages with advanced filtering and pagination.

    Query Parameters:
    - start_date: ISO date format (2024-01-15)
    - end_date: ISO date format
    - user: Exact sender name match
    - keyword: Substring search in message text
    - sentiment: One of [Positive, Negative, Neutral]
    - language: Language code (en, hi, es, fr, etc.)
    - limit: 1-500 messages per page
    - page: 1-based page number

    Returns paginated results with total count.
    """
    try:
        # Validate sentiment if provided
        if sentiment and sentiment not in ["Positive", "Negative", "Neutral"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sentiment: {sentiment}. Must be Positive, Negative, or Neutral.",
            )

        # Calculate offset
        offset = (page - 1) * limit

        # Query database
        messages, total = query_messages(
            start_date=start_date,
            end_date=end_date,
            sender=user,
            keyword=keyword,
            sentiment=sentiment,
            language=language,
            limit=limit,
            offset=offset,
        )

        # Convert rows to MessageDB objects
        message_objects = []
        for msg in messages:
            # Parse JSON fields
            emotions = json.loads(msg["emotions"]) if msg["emotions"] else None
            keywords = json.loads(msg["keywords"]) if msg["keywords"] else None

            msg_obj = MessageDB(
                id=msg["id"],
                timestamp=msg["timestamp"],
                sender=msg["sender"],
                text=msg["text"],
                translated_text=msg["translated_text"],
                language=msg["language"],
                vader_score=msg["vader_score"],
                textblob_score=msg["textblob_score"],
                ensemble_score=msg["ensemble_score"],
                ensemble_label=msg["ensemble_label"],
                emotions=emotions,
                keywords=keywords,
            )
            message_objects.append(msg_obj)

        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit

        return PaginatedMessages(
            messages=message_objects,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid query parameter: {str(e)}")
    except Exception as e:
        logger.exception(f"Error querying messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@app.get("/stats", response_model=FilterStats)
async def get_filtered_stats(
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    user: Optional[str] = Query(None, description="Filter by sender name"),
):
    """
    Get statistics and aggregations over filtered messages.

    Returns:
    - Sentiment distribution (count, average score per label)
    - Language distribution
    - Top 10 participants by message count
    - Overall average sentiment score
    """
    try:
        stats = get_stats(
            start_date=start_date,
            end_date=end_date,
            sender=user,
        )
        return FilterStats(**stats)
    except Exception as e:
        logger.exception(f"Error computing stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to compute statistics")


# ============================================================================
# PHASE 3: SUMMARIZATION ENDPOINTS
# ============================================================================

@app.post("/summarize/{job_id}")
async def summarize_job(job_id: str):
    """
    Generate summaries and analysis for a completed analysis job.
    
    Returns:
    - Short summary (1-2 sentences)
    - Detailed summary (3-4 sentences)
    - Key topics extracted
    - Emotional trend analysis over time
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "complete":
        raise HTTPException(status_code=400, detail=f"Job status is {job.get('status')}, not complete")
    
    try:
        result = job.get("result", {})
        messages = result.get("messages", [])
        
        # Get all message texts
        message_texts = [msg.get("message", "") for msg in messages]
        combined_text = " ".join(message_texts)
        
        # Generate summaries
        summarization_service = get_summarization_service()
        summary = summarization_service.generate_full_analysis(messages, combined_text)
        
        return {
            "job_id": job_id,
            "message_count": len(messages),
            "analysis": summary
        }
    except Exception as e:
        logger.exception(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


# ============================================================================
# PHASE 4: MULTILINGUAL ENDPOINTS
# ============================================================================

@app.post("/translate")
async def translate_message(text: str, target_language: str = "en"):
    """
    Translate text to target language.
    
    Parameters:
    - text: Message text to translate
    - target_language: ISO 639-1 code (en, hi, es, fr, etc.)
    
    Returns:
    - Original text
    - Translated text
    - Detected source language
    - Language info
    """
    if not text or len(text) < 3:
        raise HTTPException(status_code=400, detail="Text too short to translate")
    
    try:
        multilingual_service = get_multilingual_service()
        
        # Detect source language
        source_lang, confidence = multilingual_service.detect_language(text)
        
        # Check for Hinglish
        is_hinglish = multilingual_service.detect_hinglish(text)
        hinglish_analysis = None
        if is_hinglish:
            hinglish_analysis = multilingual_service.analyze_hinglish_sentiment(text)
        
        # Translate
        translated = multilingual_service.translate_text(text, source_lang, target_language)
        
        return {
            "original_text": text,
            "translated_text": translated,
            "source_language": multilingual_service.get_language_name(source_lang),
            "source_language_code": source_lang,
            "target_language": multilingual_service.get_language_name(target_language),
            "target_language_code": target_language,
            "detection_confidence": round(confidence, 2),
            "is_hinglish": is_hinglish,
            "hinglish_analysis": hinglish_analysis
        }
    except Exception as e:
        logger.exception(f"Error translating text: {e}")
        raise HTTPException(status_code=500, detail="Translation failed")


@app.get("/language-stats/{job_id}")
async def get_language_statistics(job_id: str):
    """
    Get language statistics for all messages in a job.
    
    Returns:
    - Language distribution
    - Hinglish message count
    - Primary language
    - Language diversity score
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Job not complete")
    
    try:
        result = job.get("result", {})
        messages = result.get("messages", [])
        
        multilingual_service = get_multilingual_service()
        stats = multilingual_service.get_language_stats(messages)
        
        return {
            "job_id": job_id,
            "language_statistics": stats
        }
    except Exception as e:
        logger.exception(f"Error getting language stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get language statistics")


# ============================================================================
# PHASE 5: EXPLAINABLE AI ENDPOINTS
# ============================================================================

@app.get("/explain/{message_id}")
async def explain_sentiment(message_id: str):
    """
    Get detailed explanation of why a message got its sentiment classification.
    
    Returns:
    - Per-model analysis (VADER, TextBlob, Ensemble)
    - Model disagreements (if any)
    - Confidence metrics
    - Important words contributing to sentiment
    - Final verdict with confidence
    """
    try:
        # Query the message from database
        messages, _ = query_messages(limit=1000)
        
        message_data = None
        for msg in messages:
            if msg["id"] == message_id:
                message_data = {
                    "id": msg["id"],
                    "text": msg["text"],
                    "vader_score": msg["vader_score"],
                    "textblob_score": msg["textblob_score"],
                    "ensemble_score": msg["ensemble_score"],
                    "ensemble_label": msg["ensemble_label"]
                }
                break
        
        if not message_data:
            raise HTTPException(status_code=404, detail="Message not found")
        
        explainable_ai = get_explainable_ai_service()
        explanation = explainable_ai.generate_full_explanation(message_data)
        
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating explanation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanation")


@app.get("/disagreements/{job_id}")
async def find_model_disagreements(job_id: str):
    """
    Find all messages where sentiment models disagree.
    
    Returns:
    - List of messages with disagreements
    - For each: VADER vs TextBlob labels
    - Possible reasons for disagreement
    - Count of disagreements
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Job not complete")
    
    try:
        result = job.get("result", {})
        messages = result.get("messages", [])
        
        explainable_ai = get_explainable_ai_service()
        disagreements = []
        
        for msg in messages:
            sentiment = msg.get("sentiment", {})
            vader = sentiment.get("vader_score", 0)
            textblob = sentiment.get("textblob_score", 0)
            
            disagreement = explainable_ai.find_disagreements(vader, textblob)
            if disagreement:
                disagreements.append({
                    "message": msg.get("message", "")[:100],
                    "sender": msg.get("sender"),
                    "timestamp": msg.get("timestamp"),
                    "disagreement_info": disagreement
                })
        
        return {
            "job_id": job_id,
            "total_messages": len(messages),
            "disagreement_count": len(disagreements),
            "disagreement_rate": f"{len(disagreements) / len(messages) * 100:.1f}%" if messages else "0%",
            "disagreements": disagreements
        }
    except Exception as e:
        logger.exception(f"Error finding disagreements: {e}")
        raise HTTPException(status_code=500, detail="Failed to find disagreements")