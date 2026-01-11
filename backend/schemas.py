from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional, Any

# --- Request Schemas ---

class AnalysisRequest(BaseModel):
    chat_file: bytes


# --- Message Schemas (Phase 1) ---

class SentimentScores(BaseModel):
    vader_score: float
    textblob_score: float
    ensemble_score: float
    ensemble_label: str


class MessageDB(BaseModel):
    """Single message with full analysis from database."""
    id: str
    timestamp: str
    sender: str
    text: str
    translated_text: Optional[str] = None
    language: str
    vader_score: float
    textblob_score: float
    ensemble_score: float
    ensemble_label: str
    emotions: Optional[Dict[str, float]] = None
    keywords: Optional[List[str]] = None
    emojis: Optional[List[str]] = None
    media_urls: Optional[Dict[str, List[str]]] = None


class PaginatedMessages(BaseModel):
    """Paginated message response with metadata."""
    messages: List[MessageDB]
    total: int
    page: int
    limit: int
    total_pages: int


class FilterStats(BaseModel):
    """Statistics over filtered messages."""
    total_messages: int
    sentiment_distribution: Dict[str, Dict[str, Any]]
    language_distribution: Dict[str, int]
    top_participants: Dict[str, int]
    average_sentiment_score: float


# --- Legacy Response Schemas ---

class MessageAnalysis(BaseModel):
    datetime: str
    sender: str
    message: str
    vader_score: float
    vader_label: str
    transformer_label: str
    confidence: float


class AverageSentiment(BaseModel):
    vader_score: float


class DebugInfo(BaseModel):
    total_lines_read: int
    matched_lines: int
    sample_failed_lines: List[str]


class AnalysisResult(BaseModel):
    total_messages: int
    average_sentiment: AverageSentiment
    emotion_distribution: Dict[str, int]
    most_active_users: List[Tuple[str, int]]
    top_emojis: List[Tuple[str, int]]
    messages: List[MessageAnalysis]


class ParsingError(BaseModel):
    error: str
    debug_info: Optional[DebugInfo] = None
