"""
Enterprise-grade Sentiment Analysis Service
Supports multiple models and ensemble predictions
"""
import logging
from typing import Dict, Tuple, Any
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import numpy as np
import logging

# Try optional transformers
HAS_TRANSFORMERS = False
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except Exception:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Multi-model sentiment analysis with ensemble."""
    
    def __init__(self):
        """Initialize sentiment analyzers."""
        self.vader = SentimentIntensityAnalyzer()
        self.transformer_en = None
        self.transformer_multi = None
        # Do not auto-download heavy models during init. They will be loaded lazily when needed.
        logger.info("✓ Sentiment analyzer initialized")
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using multiple models and ensemble.
        
        Returns:
            {
                'vader_score': float (-1 to 1),
                'vader_label': str,
                'textblob_score': float (-1 to 1),
                'textblob_label': str,
                'ensemble_score': float (-1 to 1),
                'ensemble_label': str,
                'confidence': float (0 to 1)
            }
        """
        try:
            if not text.strip():
                return {
                    'vader_score': 0.0,
                    'vader_label': 'Neutral',
                    'textblob_score': 0.0,
                    'textblob_label': 'Neutral',
                    'ensemble_score': 0.0,
                    'ensemble_label': 'Neutral',
                    'confidence': 0.0
                }
            
            # VADER analysis
            vader_result = self._analyze_vader(text)
            
            # TextBlob analysis
            textblob_result = self._analyze_textblob(text)

            # Transformer analyses (optional, lazy-loaded)
            transformer_en_result = None
            transformer_multi_result = None
            try:
                self._ensure_transformers()
                if self.transformer_en:
                    transformer_en_result = self._analyze_transformer(self.transformer_en, text)
                if self.transformer_multi:
                    transformer_multi_result = self._analyze_transformer(self.transformer_multi, text, multilingual=True)
            except Exception:
                # If transformer loading or analysis fails, continue with available results
                transformer_en_result = None
                transformer_multi_result = None
            
            # Ensemble (only pass vader and textblob, not transformer args)
            ensemble = self._ensemble_scores(vader_result, textblob_result)
            
            return {
                'vader_score': vader_result['score'],
                'vader_label': vader_result['label'],
                'textblob_score': textblob_result['score'],
                'textblob_label': textblob_result['label'],
                'ensemble_score': ensemble['score'],
                'ensemble_label': ensemble['label'],
                'confidence': ensemble['confidence'],
                'transformer_en': transformer_en_result,
                'transformer_multi': transformer_multi_result
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'vader_score': 0.0,
                'vader_label': 'Neutral',
                'textblob_score': 0.0,
                'textblob_label': 'Neutral',
                'ensemble_score': 0.0,
                'ensemble_label': 'Neutral',
                'confidence': 0.0
            }
    
    def _analyze_vader(self, text: str) -> Dict[str, Any]:
        """VADER sentiment analysis."""
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']
        
        if compound >= 0.05:
            label = 'Positive'
        elif compound <= -0.05:
            label = 'Negative'
        else:
            label = 'Neutral'
        
        return {'score': compound, 'label': label}

    def _ensure_transformers(self):
        """Lazy-load transformer pipelines if transformers package is available."""
        if not HAS_TRANSFORMERS:
            return
        if self.transformer_en is None:
            try:
                self.transformer_en = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
            except Exception as e:
                logger.warning(f"Failed to load English transformer pipeline: {e}")
                self.transformer_en = None
        if self.transformer_multi is None:
            try:
                self.transformer_multi = pipeline('sentiment-analysis', model='nlptown/bert-base-multilingual-uncased-sentiment')
            except Exception as e:
                logger.warning(f"Failed to load multilingual transformer pipeline: {e}")
                self.transformer_multi = None

    def _analyze_transformer(self, pipe, text: str, multilingual: bool = False) -> Dict[str, Any]:
        """Run a transformer sentiment pipeline and normalize output to {'score', 'label'}."""
        try:
            out = pipe(text[:512]) if callable(pipe) else None
            if not out:
                return None
            if isinstance(out, list) and len(out) > 0:
                item = out[0]
                label = item.get('label', '')
                score = float(item.get('score', 0.0))
                # Normalize: positive => score, negative => -score
                lab_lower = label.lower()
                if 'neg' in lab_lower or 'negative' in lab_lower or lab_lower.startswith('1'):
                    norm = -score
                else:
                    norm = score
                return {'score': norm, 'label': label}
            return None
        except Exception as e:
            logger.warning(f"Transformer analysis failed: {e}")
            return None
    
    def _analyze_textblob(self, text: str) -> Dict[str, Any]:
        """TextBlob sentiment analysis."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            if polarity > 0.1:
                label = 'Positive'
            elif polarity < -0.1:
                label = 'Negative'
            else:
                label = 'Neutral'
            
            return {'score': polarity, 'label': label}
        except Exception as e:
            logger.warning(f"TextBlob analysis failed: {e}")
            return {'score': 0.0, 'label': 'Neutral'}
    
    def _ensemble_scores(self, vader: Dict, textblob: Dict) -> Dict[str, Any]:
        """Ensemble multiple sentiment scores."""
        # Accept optional transformer results passed via *args
        def _to_score(val):
            # Expect dict like {'score': float, 'label': str} or pipeline-like {'label','score'}
            if not val:
                return 0.0
            if isinstance(val, dict) and 'score' in val:
                return float(val['score'])
            # Accept transformer pipeline output
            if isinstance(val, list) and len(val) > 0 and 'score' in val[0]:
                lab = val[0].get('label', '').lower()
                sc = float(val[0].get('score', 0.0))
                if 'neg' in lab or 'negative' in lab:
                    return -sc
                return sc
            return 0.0

        vader_norm = _to_score(vader)
        textblob_norm = _to_score(textblob)
        transformer_en = None
        transformer_multi = None
        # Extract optional transformers from kwargs if provided
        # The signature for this function may receive extra args
        # We'll check attributes on self for available pipelines
        # Weighted average: assign weights dynamically
        scores = [(vader_norm, 0.5), (textblob_norm, 0.25)]
        try:
            # if transformer pipelines exist, include them with lesser weight
            if self.transformer_en:
                # we'll fetch a normalized score in caller via passed parameter
                pass
        except Exception:
            pass

        # Fallback simple average using the weights above
        ensemble_score = vader_norm * 0.6 + textblob_norm * 0.4
        
        if ensemble_score >= 0.05:
            label = 'Positive'
        elif ensemble_score <= -0.05:
            label = 'Negative'
        else:
            label = 'Neutral'
        
        # Confidence based on agreement between models (simple heuristic)
        try:
            agreement = 1.0 - (abs(vader_norm - textblob_norm) / 2)
            confidence = abs(ensemble_score) * max(0.0, min(1.0, agreement))
        except Exception:
            confidence = abs(ensemble_score)
        
        return {
            'score': ensemble_score,
            'label': label,
            'confidence': min(confidence, 1.0)
        }


# Global instance
sentiment_analyzer = SentimentAnalyzer()
