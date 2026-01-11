"""
WhatsApp Sentiment Analyzer v2.0 - Production-Grade Backend
Refactored with persistent job storage, emoji analytics, media detection, and robust error handling.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.services.nlp_service import nlp_service
from backend.schemas_v2 import (
    JobStatus, JobStatistics, Message, PaginatedMessages,
    EmojiAnalytics, MediaAnalytics, Summary, SentimentExplanation,
    ErrorResponse, SuccessResponse, ParsingError, MessageFilter
)
from backend.database_v2 import (
    init_db, create_job, update_job_status, get_job, get_job_statistics,
    insert_message, query_messages_advanced, get_message_by_id,
    upsert_emoji, record_emoji_sender, get_emoji_analytics,
    insert_media, get_media_analytics,
    save_summary, get_summary
)
from backend.services.summarization_service import get_summarization_service
from backend.services.multilingual_service import get_multilingual_service
from backend.services.explainable_ai_service import get_explainable_ai_service
from uuid import uuid4
import logging
import traceback
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json
import re
import time
from html import unescape

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database
init_db()

app = FastAPI(
    title="WhatsApp Sentiment Analyzer v2.0",
    description="Production-grade sentiment analysis with emoji & media analytics",
    version="2.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_LANGUAGES = ["en", "hi", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ko", "ar"]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_message_type(text: str) -> Tuple[str, bool, bool, bool]:
    """
    Detect message type: text, media, emoji_only, link, document
    Returns: (message_type, is_media, is_emoji_only, is_link)
    """
    if not text:
        return "text", False, False, False
    
    text_lower = text.lower()
    
    # Check for media omitted
    if "<media omitted>" in text_lower or "image omitted" in text_lower or "video omitted" in text_lower:
        return "media", True, False, False
    
    # Check for links
    link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    has_link = bool(re.search(link_pattern, text))
    if has_link:
        return "link", False, False, True
    
    # Check for emoji-only
    emoji_pattern = r'[\U0001F300-\U0001F9FF]+|[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]'
    emojis = re.findall(emoji_pattern, text)
    non_emoji_text = re.sub(emoji_pattern, "", text).strip()
    
    if emojis and not non_emoji_text:
        return "emoji_only", False, True, False
    
    # Check for document extensions
    doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
    if any(ext in text_lower for ext in doc_extensions):
        return "document", True, False, False
    
    return "text", False, False, False


def extract_emojis(text: str) -> List[str]:
    """Extract all emojis from text."""
    if not text:
        return []
    
    emoji_pattern = r'[\U0001F300-\U0001F9FF]+|[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\u2600-\u27BF]|[\u2300-\u23FF]|[\u2000-\u206F]'
    emojis = re.findall(emoji_pattern, text)
    return list(set(emojis))  # Remove duplicates


def detect_media_types(text: str) -> Tuple[List[str], int]:
    """Detect media types mentioned in message."""
    media_types = []
    
    if "<media omitted>" in text.lower():
        # Could be any media type - mark as generic
        media_types.append("media")
    elif "image" in text.lower():
        media_types.append("image")
    elif "video" in text.lower():
        media_types.append("video")
    elif "audio" in text.lower() or "voice" in text.lower():
        media_types.append("audio")
    elif "document" in text.lower() or "file" in text.lower():
        media_types.append("document")
    
    return media_types, len(media_types)


def normalize_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Normalize various timestamp formats to ISO datetime.
    Handles: MM/DD/YYYY HH:MM, DD/MM/YYYY HH:MM, YYYY-MM-DD HH:MM, etc.
    """
    formats = [
        "%m/%d/%Y, %H:%M",  # 12/25/2023, 14:30
        "%m/%d/%Y, %H:%M:%S",
        "%d/%m/%Y, %H:%M",  # 25/12/2023, 14:30
        "%d/%m/%Y, %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%y, %H:%M",
        "%d/%m/%y, %H:%M",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not normalize timestamp: {timestamp_str}")
    return None


def sanitize_text(text: str) -> str:
    """Clean and sanitize message text."""
    if not text:
        return ""
    
    # Remove HTML entities
    text = unescape(text)
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    return text


# ============================================================================
# BACKGROUND ANALYSIS TASK
# ============================================================================

def run_analysis_task(job_id: str, content: str, filename: str):
    """
    Background task: parse chat, analyze sentiment, store in database.
    Includes chunking for large files and comprehensive error handling.
    """
    task_start = time.time()
    logger.info(f"🔄 Starting analysis for job {job_id} - {filename}")
    
    try:
        # Create job record
        if not create_job(job_id, filename):
            raise Exception("Failed to create job record")
        
        # Parse chat with NLP service
        logger.info(f"📝 Parsing chat content for job {job_id}")
        parse_result = nlp_service.analyze_chat(content)
        
        # Handle parsing errors
        if isinstance(parse_result, dict) and parse_result.get('error'):
            error_msg = parse_result.get('error')
            debug_info = parse_result.get('debug_info', {})
            
            logger.error(f"✗ Parse error for job {job_id}: {error_msg}")
            update_job_status(
                job_id, "failed",
                error_message=error_msg,
                total_messages=debug_info.get('total_lines_read', 0)
            )
            return
        
        messages = parse_result.get('messages', [])
        logger.info(f"✓ Parsed {len(messages)} messages for job {job_id}")
        
        # Store messages with comprehensive analysis
        stored_count = 0
        failed_count = 0
        
        for idx, msg in enumerate(messages):
            try:
                # Extract core data
                timestamp = normalize_timestamp(msg.get('timestamp', ''))
                if not timestamp:
                    logger.warning(f"Could not normalize timestamp: {msg.get('timestamp')}")
                    timestamp = datetime.now()
                
                raw_text = msg.get('message', '')
                cleaned_text = sanitize_text(raw_text)
                message_type, is_media, is_emoji_only, is_link = detect_message_type(raw_text)
                emojis = extract_emojis(raw_text)
                media_types, media_count = detect_media_types(raw_text)
                
                # Generate message ID
                message_id = f"{job_id}_{timestamp.isoformat()}_{msg.get('sender', 'Unknown').replace(' ', '_')}"
                
                # Extract sentiment scores
                sentiment = msg.get('sentiment', {})
                emotions = msg.get('emotions', {})
                keywords = msg.get('keywords', [])
                
                # Determine top emotion
                top_emotion = max(emotions.items(), key=lambda x: x[1])[0] if emotions else None
                
                # Store message
                success = insert_message(
                    message_id=message_id,
                    job_id=job_id,
                    timestamp=timestamp,
                    sender=msg.get('sender', 'Unknown'),
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    translated_text=msg.get('translated_message'),
                    message_type=message_type,
                    is_media=is_media,
                    is_emoji_only=is_emoji_only,
                    is_link=is_link,
                    detected_language=msg.get('language', 'en'),
                    language_confidence=msg.get('language_confidence', 0.0),
                    vader_score=sentiment.get('vader_score', 0.0),
                    vader_label=sentiment.get('vader_label', 'Neutral'),
                    textblob_score=sentiment.get('textblob_score', 0.0),
                    textblob_label=sentiment.get('textblob_label', 'Neutral'),
                    ensemble_score=sentiment.get('ensemble_score', 0.0),
                    ensemble_label=sentiment.get('ensemble_label', 'Neutral'),
                    confidence_score=sentiment.get('confidence', 0.0),
                    emotions=emotions,
                    top_emotion=top_emotion,
                    keywords=keywords,
                    emoji_list=emojis,
                    media_types=media_types,
                    media_count=media_count,
                    toxicity_score=msg.get('toxicity_score', 0.0),
                    is_toxic=msg.get('is_toxic', False),
                )
                
                if success:
                    stored_count += 1
                    
                    # Record emojis
                    for emoji in emojis:
                        emoji_id = upsert_emoji(job_id, emoji)
                        if emoji_id:
                            record_emoji_sender(emoji_id, msg.get('sender', 'Unknown'))
                    
                    # Record media
                    if media_count > 0:
                        for i, media_type in enumerate(media_types):
                            media_id = f"{message_id}_{i}"
                            insert_media(media_id, job_id, message_id, msg.get('sender', 'Unknown'), media_type)
                else:
                    failed_count += 1
                    logger.warning(f"Failed to store message {message_id}")
                
                # Log progress
                if (idx + 1) % 100 == 0:
                    logger.info(f"📊 Progress: {idx + 1}/{len(messages)} messages processed")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Error processing message {idx}: {e}")
                continue
        
        logger.info(f"✓ Stored {stored_count}/{len(messages)} messages (failed: {failed_count})")
        
        # Calculate overall sentiment
        if stored_count > 0:
            ensemble_scores = [msg.get('sentiment', {}).get('ensemble_score', 0.0) for msg in messages[:stored_count]]
            overall_score = sum(ensemble_scores) / len(ensemble_scores) if ensemble_scores else 0.0
            overall_label = "Positive" if overall_score > 0.1 else ("Negative" if overall_score < -0.1 else "Neutral")
        else:
            overall_score = 0.0
            overall_label = "Neutral"
        
        # Update job status
        processing_time = time.time() - task_start
        update_job_status(
            job_id, "completed",
            total_messages=len(messages),
            parsed_messages=stored_count,
            overall_sentiment_score=overall_score,
            overall_sentiment_label=overall_label,
            processing_time_seconds=processing_time
        )
        
        logger.info(f"✅ Job {job_id} completed in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"✗ Analysis failed for job {job_id}: {e}")
        logger.error(traceback.format_exc())
        
        update_job_status(
            job_id, "failed",
            error_message=str(e),
            error_traceback=traceback.format_exc()
        )


# ============================================================================
# API ENDPOINTS - ANALYSIS & UPLOADS
# ============================================================================

@app.post("/analyze", status_code=202, response_model=Dict[str, str])
async def analyze_chat_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and analyze a WhatsApp chat export file.
    Returns job_id for polling analysis status.
    """
    logger.info(f"📥 New upload: {file.filename}")
    
    # Validate filename
    if not file.filename or not file.filename.lower().endswith(".txt"):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported. Please export your WhatsApp chat as .txt"
        )
    
    try:
        # Read file
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
            )
        
        # Decode
        try:
            chat_content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            chat_content = file_content.decode("utf-8", errors='replace')
            logger.warning("File had encoding issues, decoded with replacement")
        
        # Validate content
        if len(chat_content.strip()) == 0:
            raise HTTPException(status_code=400, detail="File contains no readable text.")
        
        # Create analysis job
        job_id = str(uuid4())
        background_tasks.add_task(run_analysis_task, job_id, chat_content, file.filename)
        
        logger.info(f"✓ Job {job_id} queued for analysis")
        return {"job_id": job_id, "status": "processing"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process upload")


# ============================================================================
# API ENDPOINTS - JOB STATUS & RESULTS
# ============================================================================

@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of an analysis job."""
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatus(**{
        **job,
        "created_at": datetime.fromisoformat(job["created_at"]),
        "completed_at": datetime.fromisoformat(job["completed_at"]) if job.get("completed_at") else None
    })


@app.get("/results/{job_id}", response_model=Dict[str, Any])
async def get_analysis_results(job_id: str):
    """
    Get analysis results for a completed job.
    Polls job status and returns results when complete.
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job.get("status")
    
    if status == "processing":
        return {"status": "processing", "job_id": job_id}
    
    if status == "failed":
        raise HTTPException(
            status_code=400,
            detail=job.get("error_message") or "Analysis failed"
        )
    
    if status == "completed":
        # Return comprehensive results
        stats = get_job_statistics(job_id)
        emoji_stats = get_emoji_analytics(job_id)
        media_stats = get_media_analytics(job_id)
        summary = get_summary(job_id)
        
        return {
            "status": "complete",
            "job_id": job_id,
            "job": job,
            "statistics": stats,
            "emoji_analytics": emoji_stats,
            "media_analytics": media_stats,
            "summary": summary
        }
    
    raise HTTPException(status_code=400, detail="Unknown job status")


# ============================================================================
# API ENDPOINTS - MESSAGE FILTERING & SEARCH
# ============================================================================

@app.get("/messages", response_model=PaginatedMessages)
async def get_messages(
    job_id: str = Query(..., description="Analysis job ID"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    sender: Optional[str] = Query(None, description="Filter by sender name"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    sentiment: Optional[str] = Query(None, description="Positive/Negative/Neutral"),
    language: Optional[str] = Query(None, description="Language code (en, hi, es...)"),
    message_type: Optional[str] = Query(None, description="text/media/emoji_only/link"),
    is_toxic: Optional[bool] = Query(None, description="Filter toxic messages"),
    limit: int = Query(50, ge=1, le=500),
    page: int = Query(1, ge=1),
):
    """
    Advanced message filtering with pagination.
    Supports multiple filters and sorting.
    """
    logger.info(f"🔍 Query: job={job_id}, page={page}, limit={limit}")
    
    offset = (page - 1) * limit
    messages, total = query_messages_advanced(
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        sender=sender,
        keyword=keyword,
        sentiment=sentiment,
        language=language,
        message_type=message_type,
        is_toxic=is_toxic,
        limit=limit,
        offset=offset,
    )
    
    # Convert rows to Message objects
    message_objects = []
    for msg in messages:
        try:
            message_objects.append(Message(
                message_id=msg.get("message_id"),
                timestamp=datetime.fromisoformat(msg.get("timestamp")),
                sender=msg.get("sender"),
                raw_text=msg.get("raw_text"),
                cleaned_text=msg.get("cleaned_text"),
                translated_text=msg.get("translated_text"),
                message_type=msg.get("message_type", "text"),
                is_media=bool(msg.get("is_media")),
                is_emoji_only=bool(msg.get("is_emoji_only")),
                is_link=bool(msg.get("is_link")),
                detected_language=msg.get("detected_language", "en"),
                language_confidence=msg.get("language_confidence", 0.0),
                sentiment={
                    "vader_score": msg.get("vader_score", 0.0),
                    "vader_label": msg.get("vader_label", "Neutral"),
                    "textblob_score": msg.get("textblob_score", 0.0),
                    "textblob_label": msg.get("textblob_label", "Neutral"),
                    "ensemble_score": msg.get("ensemble_score", 0.0),
                    "ensemble_label": msg.get("ensemble_label", "Neutral"),
                    "confidence": msg.get("confidence_score", 0.0),
                },
                emotions=json.loads(msg.get("emotions")) if msg.get("emotions") else None,
                top_emotion=msg.get("top_emotion"),
                keywords=json.loads(msg.get("keywords")) if msg.get("keywords") else None,
                emoji_list=json.loads(msg.get("emoji_list")) if msg.get("emoji_list") else None,
                media_types=json.loads(msg.get("media_types")) if msg.get("media_types") else None,
                media_count=msg.get("media_count", 0),
                toxicity_score=msg.get("toxicity_score", 0.0),
                is_toxic=bool(msg.get("is_toxic")),
            ))
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            continue
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedMessages(
        messages=message_objects,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters_applied={
            "start_date": start_date,
            "end_date": end_date,
            "sender": sender,
            "keyword": keyword,
            "sentiment": sentiment,
            "language": language,
            "message_type": message_type,
            "is_toxic": is_toxic,
        }
    )


@app.get("/message/{message_id}", response_model=Message)
async def get_message_detail(message_id: str):
    """Get detailed analysis of a single message."""
    msg = get_message_by_id(message_id)
    
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return Message(
        message_id=msg["message_id"],
        timestamp=datetime.fromisoformat(msg["timestamp"]),
        sender=msg["sender"],
        raw_text=msg["raw_text"],
        cleaned_text=msg["cleaned_text"],
        translated_text=msg["translated_text"],
        message_type=msg["message_type"],
        is_media=bool(msg["is_media"]),
        is_emoji_only=bool(msg["is_emoji_only"]),
        is_link=bool(msg["is_link"]),
        detected_language=msg["detected_language"],
        language_confidence=msg["language_confidence"],
        sentiment={
            "vader_score": msg["vader_score"],
            "vader_label": msg["vader_label"],
            "textblob_score": msg["textblob_score"],
            "textblob_label": msg["textblob_label"],
            "ensemble_score": msg["ensemble_score"],
            "ensemble_label": msg["ensemble_label"],
            "confidence": msg["confidence_score"],
        },
        emotions=json.loads(msg["emotions"]) if msg["emotions"] else None,
        top_emotion=msg["top_emotion"],
        keywords=json.loads(msg["keywords"]) if msg["keywords"] else None,
        emoji_list=json.loads(msg["emoji_list"]) if msg["emoji_list"] else None,
        media_types=json.loads(msg["media_types"]) if msg["media_types"] else None,
        media_count=msg["media_count"],
        toxicity_score=msg["toxicity_score"],
        is_toxic=bool(msg["is_toxic"]),
    )


# ============================================================================
# API ENDPOINTS - ANALYTICS
# ============================================================================

@app.get("/stats/{job_id}", response_model=JobStatistics)
async def get_statistics(job_id: str):
    """Get comprehensive statistics for a job."""
    stats = get_job_statistics(job_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Job not found or no data")
    
    return JobStatistics(**stats)


@app.get("/emoji-stats/{job_id}", response_model=EmojiAnalytics)
async def get_emoji_analytics_endpoint(
    job_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get detailed emoji analytics for a job."""
    emojis = get_emoji_analytics(job_id, limit)
    
    if not emojis:
        return EmojiAnalytics(
            job_id=job_id,
            total_emojis_used=0,
            unique_emojis=0,
            top_emojis=[],
            emoji_distribution={},
            user_emoji_preferences={}
        )
    
    # Convert to API format
    emoji_items = []
    emoji_distribution = {}
    user_prefs = {}
    
    for emoji in emojis:
        emoji_char = emoji.get("emoji_char")
        usage_count = emoji.get("usage_count", 0)
        
        emoji_distribution[emoji_char] = usage_count
        
        # Parse user list
        user_list = []
        if emoji.get("user_list"):
            user_list = emoji["user_list"].split(",")
        
        for user in user_list:
            if user not in user_prefs:
                user_prefs[user] = []
            user_prefs[user].append(emoji_char)
        
        emoji_items.append({
            "emoji_char": emoji_char,
            "emoji_name": emoji.get("emoji_name"),
            "emoji_category": emoji.get("emoji_category"),
            "usage_count": usage_count,
            "unique_users": emoji.get("unique_users", 0),
            "user_list": user_list,
            "first_used": emoji.get("first_used"),
            "last_used": emoji.get("last_used"),
        })
    
    return EmojiAnalytics(
        job_id=job_id,
        total_emojis_used=sum(emoji_distribution.values()),
        unique_emojis=len(emoji_distribution),
        top_emojis=emoji_items,
        emoji_distribution=emoji_distribution,
        user_emoji_preferences=user_prefs
    )


@app.get("/media-stats/{job_id}", response_model=MediaAnalytics)
async def get_media_analytics_endpoint(job_id: str):
    """Get detailed media analytics for a job."""
    stats = get_media_analytics(job_id)
    
    return MediaAnalytics(
        job_id=job_id,
        total_media=stats.get("total_media", 0),
        media_by_type=stats.get("media_by_type", {}),
        top_senders=stats.get("top_senders", {}),
    )


# ============================================================================
# API ENDPOINTS - SUMMARIZATION
# ============================================================================

@app.post("/summarize/{job_id}", response_model=Summary)
async def summarize_chat(job_id: str):
    """
    Generate conversation summary.
    Includes short/detailed summary, key topics, emotional trends.
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job status is {job.get('status')}, must be 'completed'"
        )
    
    try:
        # Check cache
        cached_summary = get_summary(job_id)
        if cached_summary:
            logger.info(f"✓ Using cached summary for job {job_id}")
            return Summary(
                job_id=job_id,
                short_summary=cached_summary.get("short_summary"),
                detailed_summary=cached_summary.get("detailed_summary"),
                key_topics=json.loads(cached_summary.get("key_topics")) if cached_summary.get("key_topics") else [],
                emotional_trend=json.loads(cached_summary.get("emotional_trend")) if cached_summary.get("emotional_trend") else [],
                sentiment_timeline=json.loads(cached_summary.get("sentiment_timeline")) if cached_summary.get("sentiment_timeline") else None,
                top_keywords=json.loads(cached_summary.get("top_keywords")) if cached_summary.get("top_keywords") else [],
                generated_at=datetime.fromisoformat(cached_summary.get("created_at")),
            )
        
        # Generate new summary
        logger.info(f"📝 Generating summary for job {job_id}")
        
        # Get all messages
        messages, _ = query_messages_advanced(job_id=job_id, limit=10000)
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages found for job")
        
        # Prepare message data
        message_texts = [msg.get("raw_text", "") for msg in messages]
        combined_text = "\n".join(message_texts)
        
        # Generate summary using summarization service
        summarization_service = get_summarization_service()
        summary_data = summarization_service.generate_full_analysis(messages, combined_text)
        
        # Save summary
        summary_id = f"{job_id}_summary"
        save_summary(
            summary_id=summary_id,
            job_id=job_id,
            short_summary=summary_data.get("short_summary"),
            detailed_summary=summary_data.get("detailed_summary"),
            key_topics=summary_data.get("key_topics"),
            emotional_trend=summary_data.get("emotional_trend"),
            top_keywords=summary_data.get("top_keywords"),
        )
        
        logger.info(f"✓ Summary generated and cached for job {job_id}")
        
        return Summary(
            job_id=job_id,
            short_summary=summary_data.get("short_summary"),
            detailed_summary=summary_data.get("detailed_summary"),
            key_topics=summary_data.get("key_topics", []),
            emotional_trend=summary_data.get("emotional_trend", []),
            sentiment_timeline=summary_data.get("sentiment_timeline"),
            top_keywords=summary_data.get("top_keywords", []),
            generated_at=datetime.now(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Summarization failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


# ============================================================================
# API ENDPOINTS - EXPLAINABILITY
# ============================================================================

@app.get("/explain/{message_id}", response_model=SentimentExplanation)
async def explain_sentiment(message_id: str):
    """
    Get detailed explanation of message sentiment classification.
    Shows per-model scores, disagreements, and important words.
    """
    msg = get_message_by_id(message_id)
    
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    try:
        explainable_ai = get_explainable_ai_service()
        
        # Build message data for explanation
        message_data = {
            "message_id": msg["message_id"],
            "text": msg["raw_text"],
            "sender": msg["sender"],
            "timestamp": msg["timestamp"],
            "vader_score": msg["vader_score"],
            "vader_label": msg["vader_label"],
            "textblob_score": msg["textblob_score"],
            "textblob_label": msg["textblob_label"],
            "ensemble_score": msg["ensemble_score"],
            "ensemble_label": msg["ensemble_label"],
        }
        
        explanation = explainable_ai.generate_full_explanation(message_data)
        
        return SentimentExplanation(
            message_id=message_id,
            message_text=msg["raw_text"],
            sender=msg["sender"],
            timestamp=datetime.fromisoformat(msg["timestamp"]),
            model_explanations=[
                {
                    "model_name": "VADER",
                    "score": msg["vader_score"],
                    "label": msg["vader_label"],
                    "confidence": 0.85,
                },
                {
                    "model_name": "TextBlob",
                    "score": msg["textblob_score"],
                    "label": msg["textblob_label"],
                    "confidence": 0.80,
                },
                {
                    "model_name": "Ensemble",
                    "score": msg["ensemble_score"],
                    "label": msg["ensemble_label"],
                    "confidence": msg.get("confidence_score", 0.85),
                },
            ],
            disagreements=explanation.get("disagreements"),
            important_words=explanation.get("important_words", []),
            final_verdict=explanation.get("verdict", msg["ensemble_label"]),
            overall_confidence=msg.get("confidence_score", 0.85),
        )
        
    except Exception as e:
        logger.error(f"✗ Explanation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanation")


@app.get("/disagreements/{job_id}")
async def find_disagreements(job_id: str):
    """
    Find messages where sentiment models disagree.
    Returns list of conflicting predictions.
    """
    try:
        # Get all messages for job
        messages, _ = query_messages_advanced(job_id=job_id, limit=10000)
        
        disagreements = []
        
        for msg in messages:
            vader_label = msg.get("vader_label")
            textblob_label = msg.get("textblob_label")
            ensemble_label = msg.get("ensemble_label")
            
            # Check for disagreements
            if vader_label != textblob_label or vader_label != ensemble_label:
                disagreements.append({
                    "message_id": msg["message_id"],
                    "text": msg["raw_text"][:100],
                    "sender": msg["sender"],
                    "vader": {
                        "label": vader_label,
                        "score": msg["vader_score"],
                    },
                    "textblob": {
                        "label": textblob_label,
                        "score": msg["textblob_score"],
                    },
                    "ensemble": {
                        "label": ensemble_label,
                        "score": msg["ensemble_score"],
                    },
                })
        
        return {
            "job_id": job_id,
            "total_messages": len(messages),
            "disagreement_count": len(disagreements),
            "disagreement_rate": f"{len(disagreements) / len(messages) * 100:.1f}%" if messages else "0%",
            "disagreements": disagreements,
        }
        
    except Exception as e:
        logger.error(f"✗ Disagreement analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze disagreements")


# ============================================================================
# HEALTH CHECK & INFO
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    """API information."""
    return {
        "name": "WhatsApp Sentiment Analyzer v2.0",
        "version": "2.0.0",
        "description": "Production-grade sentiment analysis with emoji & media analytics",
        "endpoints": {
            "upload": "POST /analyze",
            "status": "GET /job/{job_id}",
            "results": "GET /results/{job_id}",
            "messages": "GET /messages",
            "statistics": "GET /stats/{job_id}",
            "emoji_analytics": "GET /emoji-stats/{job_id}",
            "media_analytics": "GET /media-stats/{job_id}",
            "summarize": "POST /summarize/{job_id}",
            "explain": "GET /explain/{message_id}",
            "disagreements": "GET /disagreements/{job_id}",
            "health": "GET /health",
        },
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
