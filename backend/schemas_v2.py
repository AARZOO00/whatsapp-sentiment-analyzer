"""
Enhanced Pydantic Schemas v2.0 - Rich message types and API responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to analyze a chat file."""
    chat_file: bytes
    filename: str = "chat.txt"


# ============================================================================
# MESSAGE SCHEMAS
# ============================================================================

class Sentiment(BaseModel):
    """Sentiment scores from multiple models."""
    vader_score: float = Field(..., ge=-1.0, le=1.0)
    vader_label: str
    textblob_score: float = Field(..., ge=-1.0, le=1.0)
    textblob_label: str
    ensemble_score: float = Field(..., ge=-1.0, le=1.0)
    ensemble_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class Message(BaseModel):
    """Comprehensive message with full NLP analysis."""
    message_id: str
    timestamp: datetime
    sender: str
    raw_text: str
    cleaned_text: Optional[str] = None
    translated_text: Optional[str] = None
    message_type: str = "text"  # text, media, emoji_only, link, document
    is_media: bool = False
    is_emoji_only: bool = False
    is_link: bool = False
    detected_language: str = "en"
    language_confidence: float = 0.0
    sentiment: Sentiment
    emotions: Optional[Dict[str, float]] = None
    top_emotion: Optional[str] = None
    keywords: Optional[List[tuple]] = None
    emoji_list: Optional[List[str]] = None
    media_types: Optional[List[str]] = None
    media_count: int = 0
    toxicity_score: float = 0.0
    is_toxic: bool = False


class PaginatedMessages(BaseModel):
    """Paginated message response."""
    messages: List[Message]
    total: int
    page: int
    limit: int
    total_pages: int
    filters_applied: Dict[str, Any] = {}


# ============================================================================
# JOB & ANALYSIS SCHEMAS
# ============================================================================

class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: str  # processing, completed, failed
    filename: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_messages: int = 0
    parsed_messages: int = 0
    failed_lines: int = 0
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class SentimentDistribution(BaseModel):
    """Sentiment counts and averages."""
    positive: Dict[str, Any] = {}
    negative: Dict[str, Any] = {}
    neutral: Dict[str, Any] = {}


class LanguageStats(BaseModel):
    """Language distribution."""
    language_distribution: Dict[str, int] = {}
    primary_language: Optional[str] = None
    language_diversity_score: float = 0.0


class MessageTypeStats(BaseModel):
    """Message type breakdown."""
    text_messages: int = 0
    media_messages: int = 0
    emoji_only_messages: int = 0
    link_messages: int = 0
    document_messages: int = 0


class ToxicityStats(BaseModel):
    """Toxicity analysis."""
    total_messages: int = 0
    toxic_messages: int = 0
    toxicity_rate: float = 0.0


class JobStatistics(BaseModel):
    """Comprehensive job statistics."""
    job_id: str
    total_messages: int
    overall_sentiment_score: float
    overall_sentiment_label: str
    sentiment_distribution: SentimentDistribution
    language_stats: LanguageStats
    message_type_stats: MessageTypeStats
    toxicity_stats: ToxicityStats
    top_senders: List[Dict[str, Any]] = []
    top_keywords: List[tuple] = []
    top_emotions: Dict[str, int] = {}


# ============================================================================
# EMOJI ANALYTICS SCHEMAS
# ============================================================================

class EmojiInfo(BaseModel):
    """Single emoji with stats."""
    emoji_char: str
    emoji_name: Optional[str] = None
    emoji_category: Optional[str] = None
    usage_count: int
    unique_users: int
    user_list: Optional[List[str]] = None
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None


class EmojiAnalytics(BaseModel):
    """Emoji analytics for a job."""
    job_id: str
    total_emojis_used: int
    unique_emojis: int
    top_emojis: List[EmojiInfo]
    emoji_distribution: Dict[str, int]
    user_emoji_preferences: Dict[str, List[str]]


# ============================================================================
# MEDIA ANALYTICS SCHEMAS
# ============================================================================

class MediaItem(BaseModel):
    """Detected media item."""
    media_id: str
    media_type: str  # image, video, document, link, audio
    sender: str
    timestamp: datetime
    description: Optional[str] = None


class MediaAnalytics(BaseModel):
    """Media analytics for a job."""
    job_id: str
    total_media: int
    media_by_type: Dict[str, int]
    top_senders: Dict[str, int]
    media_items: List[MediaItem] = []


# ============================================================================
# SUMMARIZATION SCHEMAS
# ============================================================================

class SummarySentimentTrend(BaseModel):
    """Sentiment trend over time."""
    time_period: str
    sentiment_label: str
    percentage: float


class Summary(BaseModel):
    """Conversation summary."""
    job_id: str
    short_summary: str
    detailed_summary: str
    key_topics: List[str]
    emotional_trend: List[SummarySentimentTrend]
    sentiment_timeline: Optional[Dict[str, float]] = None
    top_keywords: List[tuple] = []
    generated_at: datetime


# ============================================================================
# EXPLAINABILITY SCHEMAS
# ============================================================================

class ModelExplanation(BaseModel):
    """Per-model sentiment explanation."""
    model_name: str
    score: float
    label: str
    confidence: float
    explanation: Optional[str] = None


class SentimentExplanation(BaseModel):
    """Full sentiment explanation with model reasoning."""
    message_id: str
    message_text: str
    sender: str
    timestamp: datetime
    model_explanations: List[ModelExplanation]
    disagreements: Optional[List[str]] = None
    important_words: List[tuple]
    final_verdict: str
    overall_confidence: float


# ============================================================================
# ERROR & RESPONSE SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    status: str = "success"
    message: str
    data: Optional[Dict[str, Any]] = None


class DebugInfo(BaseModel):
    """Parsing debug information."""
    total_lines_read: int
    matched_lines: int
    failed_lines: int
    sample_failed_lines: List[str]


class ParsingError(BaseModel):
    """Parsing error with debug info."""
    error: str
    debug_info: Optional[DebugInfo] = None
    suggestions: Optional[List[str]] = None


# ============================================================================
# FILTER & QUERY SCHEMAS
# ============================================================================

class MessageFilter(BaseModel):
    """Message filter criteria."""
    job_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    sender: Optional[str] = None
    keyword: Optional[str] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    message_type: Optional[str] = None
    is_toxic: Optional[bool] = None
    limit: int = Field(50, ge=1, le=500)
    page: int = Field(1, ge=1)
