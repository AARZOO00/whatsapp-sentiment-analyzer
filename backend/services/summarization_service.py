"""
Phase 3: Transformer-based summarization service for chat conversations.
Provides both short summaries and detailed analysis with key topics and trends.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SummarizationService:
    """Handles conversation summarization using transformer models."""
    
    def __init__(self):
        """Initialize summarization service with lazy-loaded models."""
        self.summarizer = None
        self.tagger = None
        self.initialized = False
        self._initialize_models()
    
    def _initialize_models(self):
        """Lazy load transformer models only when first needed."""
        try:
            from transformers import pipeline
            
            logger.info("Loading transformer models for summarization...")
            
            # Initialize summarization pipeline
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1,  # CPU
                truncation=True,
                max_length=150,
                min_length=30
            )
            
            # Initialize zero-shot classification for topic extraction
            self.tagger = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU
            )
            
            logger.info("✓ Summarization models loaded successfully")
            self.initialized = True
        except ImportError:
            logger.warning("Transformers not available - summarization disabled")
            self.initialized = False
        except Exception as e:
            logger.error(f"Failed to load summarization models: {e}")
            self.initialized = False
    
    def generate_short_summary(self, text: str, max_length: int = 100) -> Optional[str]:
        """
        Generate a short summary (1-2 sentences) of the conversation.
        
        Args:
            text: Combined message text
            max_length: Maximum length of summary
            
        Returns:
            Short summary string or None if failed
        """
        if not self.initialized or not text or len(text) < 50:
            return None
        
        try:
            # Ensure text is not too long (BART has token limits)
            text = text[:1024]
            
            if len(text.split()) < 10:
                return None
            
            summary = self.summarizer(text, max_length=50, min_length=15, do_sample=False)
            return summary[0]['summary_text'] if summary else None
        except Exception as e:
            logger.error(f"Error generating short summary: {e}")
            return None
    
    def generate_detailed_summary(self, text: str) -> Optional[str]:
        """
        Generate a detailed summary (3-4 sentences) of the conversation.
        
        Args:
            text: Combined message text
            
        Returns:
            Detailed summary string or None if failed
        """
        if not self.initialized or not text or len(text) < 50:
            return None
        
        try:
            text = text[:2048]
            
            if len(text.split()) < 20:
                return None
            
            summary = self.summarizer(text, max_length=150, min_length=50, do_sample=False)
            return summary[0]['summary_text'] if summary else None
        except Exception as e:
            logger.error(f"Error generating detailed summary: {e}")
            return None
    
    def extract_key_topics(self, text: str, num_topics: int = 5) -> Optional[List[str]]:
        """
        Extract key topics using zero-shot classification.
        
        Args:
            text: Combined message text
            num_topics: Number of topics to extract
            
        Returns:
            List of key topics or None if failed
        """
        if not self.initialized or not text:
            return None
        
        try:
            # Common conversation topics
            candidate_labels = [
                "greeting", "goodbye", "expressing joy", "expressing sadness",
                "asking question", "giving advice", "making plan", "complaint",
                "compliment", "discussion", "decision making", "celebration",
                "work discussion", "personal life", "relationship", "problem solving",
                "joke", "agreement", "disagreement", "confirmation"
            ]
            
            text = text[:512]  # Limit for classification
            
            # Classify the overall conversation
            result = self.tagger(text, candidate_labels, multi_class=True)
            
            # Extract top topics
            topics = result['labels'][:num_topics] if result['labels'] else []
            return topics if topics else None
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return None
    
    def analyze_emotional_trend(
        self,
        messages: List[Dict],
        time_window: int = 5
    ) -> Optional[Dict]:
        """
        Analyze emotional trend over the conversation (time-series sentiment).
        
        Args:
            messages: List of message dictionaries with 'ensemble_label' and 'timestamp'
            time_window: Number of messages per window for trend analysis
            
        Returns:
            Dictionary with trend information or None if failed
        """
        if not messages or len(messages) < 2:
            return None
        
        try:
            # Group messages by time windows
            windows = []
            sentiment_scores = []
            
            for i, msg in enumerate(messages):
                sentiment = msg.get('ensemble_label', 'Neutral')
                sentiment_scores.append(sentiment)
                
                if (i + 1) % time_window == 0 or i == len(messages) - 1:
                    window_sentiments = sentiment_scores[-(i+1)%time_window or len(sentiment_scores):]
                    positive_count = sum(1 for s in window_sentiments if s == 'Positive')
                    negative_count = sum(1 for s in window_sentiments if s == 'Negative')
                    
                    trend_direction = "positive" if positive_count > negative_count else (
                        "negative" if negative_count > positive_count else "neutral"
                    )
                    
                    windows.append({
                        "window": len(windows) + 1,
                        "messages_count": len(window_sentiments),
                        "positive": positive_count,
                        "negative": negative_count,
                        "trend": trend_direction
                    })
            
            # Determine overall trend
            if len(windows) >= 2:
                first_window = windows[0]['trend']
                last_window = windows[-1]['trend']
                
                if first_window == 'negative' and last_window == 'positive':
                    overall_trend = "improving"
                elif first_window == 'positive' and last_window == 'negative':
                    overall_trend = "declining"
                elif first_window == 'positive' or last_window == 'positive':
                    overall_trend = "mostly positive"
                else:
                    overall_trend = "mostly neutral"
            else:
                overall_trend = windows[0]['trend'] if windows else "neutral"
            
            return {
                "windows": windows,
                "overall_trend": overall_trend,
                "total_messages": len(messages),
                "windows_count": len(windows)
            }
        except Exception as e:
            logger.error(f"Error analyzing emotional trend: {e}")
            return None
    
    def generate_full_analysis(self, messages: List[Dict], text: str) -> Dict:
        """
        Generate complete conversation analysis with all summarization features.
        
        Args:
            messages: List of parsed messages
            text: Combined message text
            
        Returns:
            Dictionary with complete analysis
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "short_summary": self.generate_short_summary(text),
            "detailed_summary": self.generate_detailed_summary(text),
            "key_topics": self.extract_key_topics(text),
            "emotional_trend": self.analyze_emotional_trend(messages),
            "available": self.initialized
        }
        
        logger.info(f"Generated full analysis for {len(messages)} messages")
        return analysis


# Singleton instance
_summarization_service = None


def get_summarization_service() -> SummarizationService:
    """Get or create summarization service singleton."""
    global _summarization_service
    if _summarization_service is None:
        _summarization_service = SummarizationService()
    return _summarization_service
