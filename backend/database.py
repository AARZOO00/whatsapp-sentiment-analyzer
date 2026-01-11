"""
Database models for WhatsApp Sentiment Analyzer.
Uses SQLite for persistent message storage and analysis results.
"""
import sqlite3
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

DATABASE_FILE = "analyzer.db"


def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Messages table: stores parsed WhatsApp messages with sentiment analysis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
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
            emojis JSON,
            media_urls JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, timestamp, sender)
        )
    """)

    # Summaries table: stores conversation summaries per job
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id TEXT PRIMARY KEY,
            job_id TEXT UNIQUE,
            short_summary TEXT,
            detailed_summary TEXT,
            key_topics JSON,
            emotional_trend TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Analysis jobs table: tracks analysis requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            filename TEXT,
            status TEXT,
            total_messages INTEGER,
            overall_sentiment JSON,
            error TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
    """)

    # Create indices for faster querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment ON messages(ensemble_label)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_language ON messages(language)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job ON messages(job_id)")

    # Add missing columns if they don't exist (migration)
    cursor.execute("PRAGMA table_info(messages)")
    columns = {col[1] for col in cursor.fetchall()}
    
    if 'emojis' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN emojis JSON")
        logger.info("Added 'emojis' column to messages table")
    
    if 'media_urls' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN media_urls JSON")
        logger.info("Added 'media_urls' column to messages table")

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def insert_message(
    msg_id: str,
    job_id: str,
    timestamp: datetime,
    sender: str,
    text: str,
    translated_text: Optional[str],
    language: str,
    vader_score: float,
    textblob_score: float,
    ensemble_score: float,
    ensemble_label: str,
    emotions: str,  # JSON string
    keywords: str,  # JSON string
    emojis: Optional[str] = None,  # JSON string
    media_urls: Optional[str] = None,  # JSON string
):
    """Insert a parsed message with sentiment scores into the database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (
                id, job_id, timestamp, sender, text, translated_text,
                language, vader_score, textblob_score, ensemble_score,
                ensemble_label, emotions, keywords, emojis, media_urls
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg_id,
                job_id,
                timestamp,
                sender,
                text,
                translated_text,
                language,
                vader_score,
                textblob_score,
                ensemble_score,
                ensemble_label,
                emotions,
                keywords,
                emojis,
                media_urls,
            ),
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError as e:
        logger.warning(f"Message already exists (ignored): {e}")
    except Exception as e:
        logger.error(f"Failed to insert message: {e}")
        raise


def query_messages(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sender: Optional[str] = None,
    keyword: Optional[str] = None,
    sentiment: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Query messages with optional filters. Returns paginated results."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query dynamically
        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("timestamp >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("timestamp <= ?")
            params.append(end_date)

        if sender:
            where_clauses.append("sender = ?")
            params.append(sender)

        if keyword:
            where_clauses.append("text LIKE ?")
            params.append(f"%{keyword}%")

        if sentiment:
            where_clauses.append("ensemble_label = ?")
            params.append(sentiment)

        if language:
            where_clauses.append("language = ?")
            params.append(language)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        query = f"""
            SELECT * FROM messages
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]

        # Get total count for pagination
        count_query = f"SELECT COUNT(*) as count FROM messages WHERE {where_sql}"
        cursor.execute(count_query, params[:-2])
        total = cursor.fetchone()["count"]

        conn.close()
        return messages, total
    except Exception as e:
        logger.error(f"Failed to query messages: {e}")
        raise


def get_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sender: Optional[str] = None,
):
    """Get statistics over filtered messages."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("timestamp >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("timestamp <= ?")
            params.append(end_date)

        if sender:
            where_clauses.append("sender = ?")
            params.append(sender)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Overall sentiment distribution
        query = f"""
            SELECT
                ensemble_label,
                COUNT(*) as count,
                AVG(ensemble_score) as avg_score
            FROM messages
            WHERE {where_sql}
            GROUP BY ensemble_label
        """
        cursor.execute(query, params)
        sentiment_dist = {row["ensemble_label"]: {"count": row["count"], "avg_score": row["avg_score"]} for row in cursor.fetchall()}

        # Language distribution
        query = f"""
            SELECT language, COUNT(*) as count
            FROM messages
            WHERE {where_sql}
            GROUP BY language
        """
        cursor.execute(query, params)
        language_dist = {row["language"]: row["count"] for row in cursor.fetchall()}

        # Top participants
        query = f"""
            SELECT sender, COUNT(*) as count
            FROM messages
            WHERE {where_sql}
            GROUP BY sender
            ORDER BY count DESC
            LIMIT 10
        """
        cursor.execute(query, params)
        top_senders = {row["sender"]: row["count"] for row in cursor.fetchall()}

        # Overall average sentiment score
        query = f"SELECT AVG(ensemble_score) as avg FROM messages WHERE {where_sql}"
        cursor.execute(query, params)
        avg_sentiment = cursor.fetchone()["avg"]

        conn.close()

        return {
            "total_messages": sum(s["count"] for s in sentiment_dist.values()),
            "sentiment_distribution": sentiment_dist,
            "language_distribution": language_dist,
            "top_participants": top_senders,
            "average_sentiment_score": round(avg_sentiment, 3) if avg_sentiment else 0.0,
        }
    except Exception as e:
        logger.error(f"Failed to compute stats: {e}")
        raise


def clear_all_messages():
    """Clear all messages from database (for testing)."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM summaries")
        cursor.execute("DELETE FROM jobs")
        conn.commit()
        conn.close()
        logger.info("All messages cleared")
    except Exception as e:
        logger.error(f"Failed to clear messages: {e}")
        raise
