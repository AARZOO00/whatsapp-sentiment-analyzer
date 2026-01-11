"""
Enhanced Database Schema v2.0 - Persistent Job Storage and Rich Analytics
Supports emoji analytics, media detection, message type classification, and better filtering.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
import logging
import json

logger = logging.getLogger(__name__)

DATABASE_FILE = "analyzer.db"


def dict_factory(cursor, row):
    """Convert database rows to dictionaries."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def init_db():
    """Initialize SQLite database with v2.0 schema including jobs, messages, emoji analytics."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    # JOBS TABLE - Persists analysis metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            status TEXT DEFAULT 'processing',
            total_messages INTEGER DEFAULT 0,
            parsed_messages INTEGER DEFAULT 0,
            failed_lines INTEGER DEFAULT 0,
            overall_sentiment_score REAL,
            overall_sentiment_label TEXT,
            error_message TEXT,
            error_traceback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            processing_time_seconds REAL
        )
    """)

    # MESSAGES TABLE - Rich message data with type classification
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            sender TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            cleaned_text TEXT,
            translated_text TEXT,
            message_type TEXT DEFAULT 'text',
            is_media BOOLEAN DEFAULT 0,
            is_emoji_only BOOLEAN DEFAULT 0,
            is_link BOOLEAN DEFAULT 0,
            detected_language TEXT DEFAULT 'en',
            language_confidence REAL,
            vader_score REAL,
            vader_label TEXT,
            textblob_score REAL,
            textblob_label TEXT,
            ensemble_score REAL,
            ensemble_label TEXT,
            confidence_score REAL,
            emotions JSON,
            top_emotion TEXT,
            keywords JSON,
            emoji_list JSON,
            media_types JSON,
            media_count INTEGER DEFAULT 0,
            toxicity_score REAL,
            is_toxic BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, timestamp, sender),
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    # EMOJI ANALYTICS TABLE - Emoji insights
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emoji_analytics (
            emoji_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            emoji_char TEXT NOT NULL,
            emoji_name TEXT,
            emoji_category TEXT,
            usage_count INTEGER DEFAULT 1,
            unique_users INTEGER DEFAULT 1,
            first_used DATETIME,
            last_used DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id),
            UNIQUE(job_id, emoji_char)
        )
    """)

    # EMOJI_SENDERS TABLE - Which users used which emojis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emoji_senders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emoji_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            FOREIGN KEY (emoji_id) REFERENCES emoji_analytics(emoji_id),
            UNIQUE(emoji_id, sender)
        )
    """)

    # MEDIA ANALYTICS TABLE - Media insights
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_analytics (
            media_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            media_type TEXT,
            description TEXT,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id),
            FOREIGN KEY (message_id) REFERENCES messages(message_id)
        )
    """)

    # SUMMARIES TABLE - Conversation summaries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            summary_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL UNIQUE,
            short_summary TEXT,
            detailed_summary TEXT,
            key_topics JSON,
            emotional_trend JSON,
            sentiment_timeline JSON,
            top_keywords JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    # CREATE INDICES for fast querying
    indices = [
        ("idx_job_id", "messages", "job_id"),
        ("idx_sender", "messages", "sender"),
        ("idx_timestamp", "messages", "timestamp"),
        ("idx_ensemble_label", "messages", "ensemble_label"),
        ("idx_language", "messages", "detected_language"),
        ("idx_message_type", "messages", "message_type"),
        ("idx_is_toxic", "messages", "is_toxic"),
        ("idx_job_status", "jobs", "status"),
        ("idx_emoji_job", "emoji_analytics", "job_id"),
        ("idx_emoji_count", "emoji_analytics", "usage_count"),
        ("idx_media_job", "media_analytics", "job_id"),
    ]

    for idx_name, table, column in indices:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")

    conn.commit()
    conn.close()
    logger.info("✓ Database v2.0 initialized successfully")


# ============================================================================
# JOB MANAGEMENT
# ============================================================================

def create_job(job_id: str, filename: str) -> bool:
    """Create a new analysis job."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (job_id, filename, status)
            VALUES (?, ?, 'processing')
        """, (job_id, filename))
        conn.commit()
        conn.close()
        logger.info(f"✓ Job created: {job_id}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create job {job_id}: {e}")
        return False


def update_job_status(job_id: str, status: str, **kwargs) -> bool:
    """Update job status and metadata."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        updates = ["status = ?"]
        params = [status]
        
        if status == "completed":
            updates.append("completed_at = CURRENT_TIMESTAMP")
        
        if "total_messages" in kwargs:
            updates.append("total_messages = ?")
            params.append(kwargs["total_messages"])
        
        if "parsed_messages" in kwargs:
            updates.append("parsed_messages = ?")
            params.append(kwargs["parsed_messages"])
        
        if "overall_sentiment_score" in kwargs:
            updates.append("overall_sentiment_score = ?")
            params.append(kwargs["overall_sentiment_score"])
        
        if "overall_sentiment_label" in kwargs:
            updates.append("overall_sentiment_label = ?")
            params.append(kwargs["overall_sentiment_label"])
        
        if "error_message" in kwargs:
            updates.append("error_message = ?")
            params.append(kwargs["error_message"])
        
        if "error_traceback" in kwargs:
            updates.append("error_traceback = ?")
            params.append(kwargs["error_traceback"])
        
        if "processing_time_seconds" in kwargs:
            updates.append("processing_time_seconds = ?")
            params.append(kwargs["processing_time_seconds"])
        
        params.append(job_id)
        
        query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        logger.info(f"✓ Job {job_id} status updated to {status}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to update job {job_id}: {e}")
        return False


def get_job(job_id: str) -> Optional[Dict]:
    """Retrieve job metadata."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        job = cursor.fetchone()
        conn.close()
        return job
    except Exception as e:
        logger.error(f"✗ Failed to retrieve job {job_id}: {e}")
        return None


# ============================================================================
# MESSAGE INSERTION & STORAGE
# ============================================================================

def insert_message(
    message_id: str,
    job_id: str,
    timestamp: datetime,
    sender: str,
    raw_text: str,
    cleaned_text: Optional[str] = None,
    translated_text: Optional[str] = None,
    message_type: str = "text",
    is_media: bool = False,
    is_emoji_only: bool = False,
    is_link: bool = False,
    detected_language: str = "en",
    language_confidence: float = 0.0,
    vader_score: float = 0.0,
    vader_label: str = "Neutral",
    textblob_score: float = 0.0,
    textblob_label: str = "Neutral",
    ensemble_score: float = 0.0,
    ensemble_label: str = "Neutral",
    confidence_score: float = 0.0,
    emotions: Optional[Dict] = None,
    top_emotion: Optional[str] = None,
    keywords: Optional[List] = None,
    emoji_list: Optional[List] = None,
    media_types: Optional[List] = None,
    media_count: int = 0,
    toxicity_score: float = 0.0,
    is_toxic: bool = False,
) -> bool:
    """Insert a message with comprehensive analysis."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO messages (
                message_id, job_id, timestamp, sender, raw_text, cleaned_text,
                translated_text, message_type, is_media, is_emoji_only, is_link,
                detected_language, language_confidence,
                vader_score, vader_label, textblob_score, textblob_label,
                ensemble_score, ensemble_label, confidence_score,
                emotions, top_emotion, keywords, emoji_list, media_types,
                media_count, toxicity_score, is_toxic
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id, job_id, timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            sender, raw_text, cleaned_text, translated_text, message_type,
            1 if is_media else 0, 1 if is_emoji_only else 0, 1 if is_link else 0,
            detected_language, language_confidence,
            vader_score, vader_label, textblob_score, textblob_label,
            ensemble_score, ensemble_label, confidence_score,
            json.dumps(emotions) if emotions else None,
            top_emotion,
            json.dumps(keywords) if keywords else None,
            json.dumps(emoji_list) if emoji_list else None,
            json.dumps(media_types) if media_types else None,
            media_count, toxicity_score, 1 if is_toxic else 0
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"✗ Failed to insert message {message_id}: {e}")
        return False


# ============================================================================
# MESSAGE QUERYING WITH FILTERS
# ============================================================================

def query_messages_advanced(
    job_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sender: Optional[str] = None,
    keyword: Optional[str] = None,
    sentiment: Optional[str] = None,
    language: Optional[str] = None,
    message_type: Optional[str] = None,
    is_toxic: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict], int]:
    """
    Advanced message filtering with multiple criteria.
    Returns: (messages, total_count)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        where_clauses = []
        params = []
        
        if job_id:
            where_clauses.append("job_id = ?")
            params.append(job_id)
        
        if start_date:
            where_clauses.append("DATE(timestamp) >= ?")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("DATE(timestamp) <= ?")
            params.append(end_date)
        
        if sender:
            where_clauses.append("sender = ?")
            params.append(sender)
        
        if keyword:
            where_clauses.append("raw_text LIKE ?")
            params.append(f"%{keyword}%")
        
        if sentiment:
            where_clauses.append("ensemble_label = ?")
            params.append(sentiment)
        
        if language:
            where_clauses.append("detected_language = ?")
            params.append(language)
        
        if message_type:
            where_clauses.append("message_type = ?")
            params.append(message_type)
        
        if is_toxic is not None:
            where_clauses.append("is_toxic = ?")
            params.append(1 if is_toxic else 0)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM messages WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        
        # Get paginated results
        query = f"""
            SELECT * FROM messages
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [limit, offset])
        messages = cursor.fetchall()
        
        conn.close()
        return messages, total
    except Exception as e:
        logger.error(f"✗ Query failed: {e}")
        return [], 0


def get_message_by_id(message_id: str) -> Optional[Dict]:
    """Get a single message by ID with all details."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,))
        message = cursor.fetchone()
        conn.close()
        return message
    except Exception as e:
        logger.error(f"✗ Failed to retrieve message {message_id}: {e}")
        return None


# ============================================================================
# EMOJI ANALYTICS
# ============================================================================

def upsert_emoji(job_id: str, emoji_char: str, emoji_name: str = None, emoji_category: str = None) -> str:
    """Add or update emoji analytics entry."""
    try:
        emoji_id = f"{job_id}_{emoji_char}"
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO emoji_analytics (emoji_id, job_id, emoji_char, emoji_name, emoji_category, first_used, last_used)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(job_id, emoji_char) DO UPDATE SET
                usage_count = usage_count + 1,
                last_used = CURRENT_TIMESTAMP
        """, (emoji_id, job_id, emoji_char, emoji_name, emoji_category))
        
        conn.commit()
        conn.close()
        return emoji_id
    except Exception as e:
        logger.error(f"✗ Failed to upsert emoji {emoji_char}: {e}")
        return None


def record_emoji_sender(emoji_id: str, sender: str) -> bool:
    """Record which user used an emoji."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO emoji_senders (emoji_id, sender, count)
            VALUES (?, ?, 1)
            ON CONFLICT(emoji_id, sender) DO UPDATE SET
                count = count + 1
        """, (emoji_id, sender))
        
        # Update unique user count in emoji_analytics
        cursor.execute("""
            UPDATE emoji_analytics SET unique_users = (
                SELECT COUNT(DISTINCT sender) FROM emoji_senders WHERE emoji_id = ?
            ) WHERE emoji_id = ?
        """, (emoji_id, emoji_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"✗ Failed to record emoji sender: {e}")
        return False


def get_emoji_analytics(job_id: str, limit: int = 50) -> List[Dict]:
    """Get emoji analytics for a job."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ea.*, 
                   (SELECT GROUP_CONCAT(sender, ',') FROM emoji_senders WHERE emoji_id = ea.emoji_id) as user_list
            FROM emoji_analytics ea
            WHERE ea.job_id = ?
            ORDER BY ea.usage_count DESC
            LIMIT ?
        """, (job_id, limit))
        
        emojis = cursor.fetchall()
        conn.close()
        return emojis
    except Exception as e:
        logger.error(f"✗ Failed to get emoji analytics: {e}")
        return []


# ============================================================================
# MEDIA ANALYTICS
# ============================================================================

def insert_media(
    media_id: str,
    job_id: str,
    message_id: str,
    sender: str,
    media_type: str,
    description: str = None
) -> bool:
    """Record detected media in a message."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO media_analytics (media_id, job_id, message_id, sender, media_type, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (media_id, job_id, message_id, sender, media_type, description))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"✗ Failed to insert media {media_id}: {e}")
        return False


def get_media_analytics(job_id: str) -> Dict[str, Any]:
    """Get media analytics for a job."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get media count by type
        cursor.execute("""
            SELECT media_type, COUNT(*) as count
            FROM media_analytics
            WHERE job_id = ?
            GROUP BY media_type
            ORDER BY count DESC
        """, (job_id,))
        
        media_by_type = {row["media_type"]: row["count"] for row in cursor.fetchall()}
        
        # Get total media count
        cursor.execute("SELECT COUNT(*) as total FROM media_analytics WHERE job_id = ?", (job_id,))
        total = cursor.fetchone()["total"]
        
        # Get top senders
        cursor.execute("""
            SELECT sender, COUNT(*) as count
            FROM media_analytics
            WHERE job_id = ?
            GROUP BY sender
            ORDER BY count DESC
            LIMIT 10
        """, (job_id,))
        
        top_senders = {row["sender"]: row["count"] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_media": total,
            "media_by_type": media_by_type,
            "top_senders": top_senders
        }
    except Exception as e:
        logger.error(f"✗ Failed to get media analytics: {e}")
        return {"total_media": 0, "media_by_type": {}, "top_senders": {}}


# ============================================================================
# AGGREGATED STATISTICS
# ============================================================================

def get_job_statistics(job_id: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a job."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get job info
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return {}
        
        # Sentiment distribution
        cursor.execute("""
            SELECT ensemble_label, COUNT(*) as count, AVG(ensemble_score) as avg_score
            FROM messages
            WHERE job_id = ?
            GROUP BY ensemble_label
        """, (job_id,))
        sentiment_dist = {row["ensemble_label"]: {"count": row["count"], "avg_score": row["avg_score"]} for row in cursor.fetchall()}
        
        # Language distribution
        cursor.execute("""
            SELECT detected_language, COUNT(*) as count
            FROM messages
            WHERE job_id = ?
            GROUP BY detected_language
            ORDER BY count DESC
        """, (job_id,))
        language_dist = {row["detected_language"]: row["count"] for row in cursor.fetchall()}
        
        # Message type distribution
        cursor.execute("""
            SELECT message_type, COUNT(*) as count
            FROM messages
            WHERE job_id = ?
            GROUP BY message_type
        """, (job_id,))
        message_type_dist = {row["message_type"]: row["count"] for row in cursor.fetchall()}
        
        # Top senders
        cursor.execute("""
            SELECT sender, COUNT(*) as count, AVG(ensemble_score) as avg_sentiment
            FROM messages
            WHERE job_id = ?
            GROUP BY sender
            ORDER BY count DESC
            LIMIT 20
        """, (job_id,))
        top_senders = [{"sender": row["sender"], "messages": row["count"], "avg_sentiment": row["avg_sentiment"]} for row in cursor.fetchall()]
        
        # Toxicity stats
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_toxic=1 THEN 1 ELSE 0 END) as toxic_count
            FROM messages
            WHERE job_id = ?
        """, (job_id,))
        toxicity = cursor.fetchone()
        
        conn.close()
        
        return {
            "job": job,
            "sentiment_distribution": sentiment_dist,
            "language_distribution": language_dist,
            "message_type_distribution": message_type_dist,
            "top_senders": top_senders,
            "toxicity": {
                "total_messages": toxicity["total"],
                "toxic_messages": toxicity["toxic_count"] or 0,
                "toxicity_rate": (toxicity["toxic_count"] or 0) / (toxicity["total"] or 1) * 100
            }
        }
    except Exception as e:
        logger.error(f"✗ Failed to get job statistics: {e}")
        return {}


# ============================================================================
# SUMMARY STORAGE
# ============================================================================

def save_summary(
    summary_id: str,
    job_id: str,
    short_summary: str = None,
    detailed_summary: str = None,
    key_topics: List = None,
    emotional_trend: Dict = None,
    sentiment_timeline: Dict = None,
    top_keywords: List = None,
) -> bool:
    """Save conversation summary to database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO summaries (
                summary_id, job_id, short_summary, detailed_summary,
                key_topics, emotional_trend, sentiment_timeline, top_keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            summary_id, job_id, short_summary, detailed_summary,
            json.dumps(key_topics) if key_topics else None,
            json.dumps(emotional_trend) if emotional_trend else None,
            json.dumps(sentiment_timeline) if sentiment_timeline else None,
            json.dumps(top_keywords) if top_keywords else None,
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"✓ Summary saved for job {job_id}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to save summary: {e}")
        return False


def get_summary(job_id: str) -> Optional[Dict]:
    """Retrieve summary for a job."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM summaries WHERE job_id = ?", (job_id,))
        summary = cursor.fetchone()
        conn.close()
        return summary
    except Exception as e:
        logger.error(f"✗ Failed to retrieve summary: {e}")
        return None
