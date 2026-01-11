"""
Phase 5: Explainable AI service providing interpretability and transparency.
Shows per-model scores, confidence metrics, word importance, and model disagreements.
"""

import logging
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class ExplainableAIService:
    """Provides explainability for AI decisions and sentiment analysis."""
    
    def __init__(self):
        """Initialize Explainable AI service."""
        self.initialized = True
        logger.info("✓ Explainable AI Service initialized")
    
    def generate_per_model_explanation(
        self,
        message: Dict,
        vader_score: float,
        textblob_score: float,
        ensemble_score: float
    ) -> Dict:
        """
        Generate per-model sentiment scores with confidence.
        
        Args:
            message: Message dictionary
            vader_score: VADER sentiment score (-1 to 1)
            textblob_score: TextBlob sentiment score (-1 to 1)
            ensemble_score: Ensemble sentiment score (-1 to 1)
            
        Returns:
            Dictionary with per-model explanations
        """
        return {
            "vader": {
                "score": round(vader_score, 3),
                "confidence": self._calculate_confidence(vader_score),
                "label": self._score_to_label(vader_score),
                "explanation": self._explain_vader_result(vader_score, message.get('text', ''))
            },
            "textblob": {
                "score": round(textblob_score, 3),
                "confidence": self._calculate_confidence(textblob_score),
                "label": self._score_to_label(textblob_score),
                "explanation": self._explain_textblob_result(textblob_score, message.get('text', ''))
            },
            "ensemble": {
                "score": round(ensemble_score, 3),
                "confidence": self._calculate_confidence(ensemble_score),
                "label": self._score_to_label(ensemble_score),
                "explanation": "Weighted combination of VADER (60%) and TextBlob (40%)"
            }
        }
    
    def _calculate_confidence(self, score: float) -> float:
        """
        Calculate confidence based on distance from neutral (0).
        Scores closer to -1 or 1 have higher confidence.
        
        Args:
            score: Sentiment score (-1 to 1)
            
        Returns:
            Confidence score (0 to 1)
        """
        return round(min(abs(score) * 1.2, 1.0), 2)  # Cap at 1.0
    
    def _score_to_label(self, score: float) -> str:
        """Convert numeric score to sentiment label."""
        if score > 0.1:
            return "Positive"
        elif score < -0.1:
            return "Negative"
        else:
            return "Neutral"
    
    def _explain_vader_result(self, score: float, text: str) -> str:
        """Generate explanation for VADER result."""
        confidence = self._calculate_confidence(score)
        
        if confidence > 0.7:
            strength = "strongly"
        elif confidence > 0.4:
            strength = "moderately"
        else:
            strength = "slightly"
        
        label = self._score_to_label(score)
        
        if label == "Positive":
            return f"VADER {strength} detects positive sentiment ({score:.2f}). " \
                   f"Uses lexicon-based approach with emphasis on positive words and punctuation."
        elif label == "Negative":
            return f"VADER {strength} detects negative sentiment ({score:.2f}). " \
                   f"Identifies negative words and intensifying punctuation marks."
        else:
            return f"VADER detects neutral sentiment ({score:.2f}). " \
                   f"Mixed sentiment cues or lacks clear sentiment indicators."
    
    def _explain_textblob_result(self, score: float, text: str) -> str:
        """Generate explanation for TextBlob result."""
        confidence = self._calculate_confidence(score)
        
        if confidence > 0.7:
            strength = "strongly"
        elif confidence > 0.4:
            strength = "moderately"
        else:
            strength = "slightly"
        
        label = self._score_to_label(score)
        
        if label == "Positive":
            return f"TextBlob {strength} detects positive sentiment ({score:.2f}). " \
                   f"Uses subjectivity and polarity analysis on word levels."
        elif label == "Negative":
            return f"TextBlob {strength} detects negative sentiment ({score:.2f}). " \
                   f"Identifies negative modifiers and sentiment-bearing words."
        else:
            return f"TextBlob detects neutral sentiment ({score:.2f}). " \
                   f"Text appears objective or lacks emotional indicators."
    
    def find_disagreements(
        self,
        vader_score: float,
        textblob_score: float
    ) -> Optional[Dict]:
        """
        Identify when models disagree on sentiment direction.
        
        Args:
            vader_score: VADER sentiment score
            textblob_score: TextBlob sentiment score
            
        Returns:
            Dictionary with disagreement info or None if models agree
        """
        vader_label = self._score_to_label(vader_score)
        textblob_label = self._score_to_label(textblob_score)
        
        if vader_label == textblob_label:
            return None  # Models agree
        
        return {
            "disagreement": True,
            "vader_says": vader_label,
            "textblob_says": textblob_label,
            "possible_reason": self._explain_disagreement(vader_score, textblob_score),
            "recommendation": "Manual review recommended for this message"
        }
    
    def _explain_disagreement(self, vader_score: float, textblob_score: float) -> str:
        """Explain why models disagree."""
        if abs(vader_score - textblob_score) > 0.5:
            return "Large difference in scores suggests mixed or complex sentiment. " \
                   "Text may contain sarcasm, irony, or both positive and negative elements."
        else:
            return "Models are close but on opposite sides of neutral. " \
                   "Text likely has subtle sentiment indicators that differ in interpretation."
    
    def extract_important_words(
        self,
        text: str,
        sentiment_type: str = 'positive'
    ) -> List[str]:
        """
        Extract words contributing to sentiment.
        
        Args:
            text: Text to analyze
            sentiment_type: 'positive', 'negative', or 'neutral'
            
        Returns:
            List of important words
        """
        sentiment_keywords = {
            'positive': ['good', 'great', 'excellent', 'amazing', 'awesome', 'love', 'happy', 
                        'wonderful', 'fantastic', 'best', 'perfect', 'beautiful', 'brilliant'],
            'negative': ['bad', 'terrible', 'awful', 'horrible', 'hate', 'sad', 'angry', 
                        'worst', 'disgusting', 'pathetic', 'disappointing', 'poor'],
            'neutral': ['think', 'believe', 'seem', 'appear', 'maybe', 'perhaps', 'might', 
                       'probably', 'possibly', 'consider', 'could']
        }
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        if sentiment_type in sentiment_keywords:
            important = [
                word for word in words 
                if word in sentiment_keywords[sentiment_type]
            ]
            return important[:10]  # Top 10
        
        return []
    
    def generate_confidence_metrics(self, message: Dict) -> Dict:
        """
        Generate comprehensive confidence metrics for a message.
        
        Args:
            message: Message dictionary with sentiment scores
            
        Returns:
            Dictionary with confidence metrics
        """
        vader = message.get('vader_score', 0)
        textblob = message.get('textblob_score', 0)
        ensemble = message.get('ensemble_score', 0)
        
        # Calculate agreement score (how much models agree)
        score_diff = abs(vader - textblob)
        agreement_score = round(max(0, 1 - (score_diff / 2)), 2)
        
        # Determine overall confidence
        if agreement_score > 0.8:
            overall_confidence = "high"
        elif agreement_score > 0.5:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"
        
        return {
            "model_agreement_score": agreement_score,
            "overall_confidence_level": overall_confidence,
            "vader_confidence": self._calculate_confidence(vader),
            "textblob_confidence": self._calculate_confidence(textblob),
            "ensemble_confidence": self._calculate_confidence(ensemble),
            "recommendation": self._get_recommendation(agreement_score, ensemble)
        }
    
    def _get_recommendation(self, agreement_score: float, ensemble_score: float) -> str:
        """Get recommendation based on confidence metrics."""
        if agreement_score > 0.8:
            return "High confidence - reliable sentiment classification"
        elif agreement_score > 0.5:
            return "Medium confidence - generally reliable with some uncertainty"
        else:
            return "Low confidence - consider manual verification for this message"
    
    def generate_full_explanation(self, message: Dict) -> Dict:
        """
        Generate complete explanation for a message's sentiment analysis.
        
        Args:
            message: Message dictionary
            
        Returns:
            Complete explanation dictionary
        """
        vader = message.get('vader_score', 0)
        textblob = message.get('textblob_score', 0)
        ensemble = message.get('ensemble_score', 0)
        text = message.get('text', '')
        
        explanation = {
            "message_id": message.get('id'),
            "text_preview": text[:100] if text else "",
            "per_model_analysis": self.generate_per_model_explanation(message, vader, textblob, ensemble),
            "disagreement": self.find_disagreements(vader, textblob),
            "confidence_metrics": self.generate_confidence_metrics(message),
            "important_words": {
                "positive_indicators": self.extract_important_words(text, 'positive'),
                "negative_indicators": self.extract_important_words(text, 'negative')
            },
            "final_verdict": {
                "sentiment": message.get('ensemble_label', 'Unknown'),
                "score": ensemble,
                "confidence": self._calculate_confidence(ensemble)
            }
        }
        
        return explanation


# Singleton instance
_explainable_ai_service = None


def get_explainable_ai_service() -> ExplainableAIService:
    """Get or create Explainable AI service singleton."""
    global _explainable_ai_service
    if _explainable_ai_service is None:
        _explainable_ai_service = ExplainableAIService()
    return _explainable_ai_service
