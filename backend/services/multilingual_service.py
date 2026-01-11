"""
Phase 4: Enhanced multilingual support with language-specific sentiment analysis.
Supports 40+ languages including Hindi, Hinglish, Urdu, Spanish, French.
"""

import logging
from typing import Dict, Optional, Tuple, List
from langdetect import detect, detect_langs, LangDetectException

try:
    from googletrans import Translator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False
    Translator = None

logger = logging.getLogger(__name__)


class MultilingualService:
    """Handles language detection, translation, and multilingual sentiment analysis."""
    
    # Supported language codes
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'zh-cn': 'Chinese (Simplified)',
        'ko': 'Korean',
        'ar': 'Arabic',
        'tr': 'Turkish',
        'pl': 'Polish',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish',
        'el': 'Greek',
        'he': 'Hebrew',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ms': 'Malay',
        'ta': 'Tamil',
        'te': 'Telugu',
        'ur': 'Urdu',
        'bn': 'Bengali',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'mr': 'Marathi',
        'pa': 'Punjabi'
    }
    
    # Language-specific sentiment keywords (Hinglish examples)
    HINGLISH_SENTIMENT_INDICATORS = {
        'positive': ['bahut acha', 'bhat', 'shukriya', 'dhanyavaad', 'awesome', 'awesome bro', 'lit', 'based'],
        'negative': ['galat', 'bura', 'bekaar', 'afsos', 'pareshaan', 'naraz', 'angry', 'upset'],
        'neutral': ['theek hai', 'ok', 'kya', 'accha']
    }
    
    def __init__(self):
        """Initialize multilingual service."""
        if HAS_GOOGLETRANS:
            self.translator = Translator()
        else:
            self.translator = None
            logger.warning("⚠ googletrans not installed - translation features disabled")
        self.cache = {}  # Simple cache for translations
        logger.info("✓ Multilingual Service initialized")
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of given text with confidence score.
        
        Args:
            text: Text to detect language from
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        if not text or len(text) < 3:
            return 'en', 0.0
        
        try:
            # Try langdetect for accurate detection
            lang = detect(text)
            
            # Get confidence by checking all probabilities
            probs = detect_langs(text)
            confidence = max([p.prob for p in probs]) if probs else 0.5
            
            return lang, confidence
        except LangDetectException:
            # Default to English if detection fails
            return 'en', 0.0
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en', 0.0
    
    def translate_text(self, text: str, source_lang: str = 'auto', target_lang: str = 'en') -> Optional[str]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (default: auto-detect)
            target_lang: Target language code (default: English)
            
        Returns:
            Translated text or None if failed
        """
        if not text or target_lang == source_lang or target_lang == 'auto':
            return text
        
        if not self.translator:
            logger.warning("Translation requested but googletrans not available - returning original text")
            return text
        
        cache_key = f"{text}:{source_lang}:{target_lang}"
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            result = self.translator.translate(
                text,
                src_language=source_lang,
                dest_language=target_lang,
                attempt_reversal=True
            )
            
            translated = result.get('text') if isinstance(result, dict) else str(result)
            
            # Cache result
            self.cache[cache_key] = translated
            
            return translated
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Get human-readable language name.
        
        Args:
            lang_code: ISO 639-1 language code
            
        Returns:
            Human-readable language name
        """
        return self.SUPPORTED_LANGUAGES.get(lang_code, f"Language ({lang_code})")
    
    def detect_hinglish(self, text: str) -> bool:
        """
        Detect if text is Hinglish (Hindi + English mix).
        
        Args:
            text: Text to check
            
        Returns:
            True if Hinglish detected
        """
        text_lower = text.lower()
        
        # Check for common Hinglish patterns
        hinglish_patterns = [
            'acha', 'bhai', 'haan', 'nahi', 'kya', 'ab', 'phir',
            'aise', 'bus', 'bas', 'theek', 'lo', 'ho', 'raha'
        ]
        
        hinglish_count = sum(1 for pattern in hinglish_patterns if pattern in text_lower)
        
        # If at least 2 Hinglish words found, it's likely Hinglish
        return hinglish_count >= 2
    
    def analyze_hinglish_sentiment(self, text: str) -> Optional[Dict]:
        """
        Analyze sentiment specifically for Hinglish text.
        
        Args:
            text: Hinglish text
            
        Returns:
            Dictionary with Hinglish sentiment indicators
        """
        text_lower = text.lower()
        
        result = {
            'positive_indicators': [],
            'negative_indicators': [],
            'neutral_indicators': [],
            'hinglish_confidence': 0.0
        }
        
        # Check for sentiment indicators
        for positive in self.HINGLISH_SENTIMENT_INDICATORS['positive']:
            if positive in text_lower:
                result['positive_indicators'].append(positive)
        
        for negative in self.HINGLISH_SENTIMENT_INDICATORS['negative']:
            if negative in text_lower:
                result['negative_indicators'].append(negative)
        
        for neutral in self.HINGLISH_SENTIMENT_INDICATORS['neutral']:
            if neutral in text_lower:
                result['neutral_indicators'].append(neutral)
        
        # Calculate Hinglish confidence
        total_indicators = len(result['positive_indicators']) + \
                          len(result['negative_indicators']) + \
                          len(result['neutral_indicators'])
        
        if total_indicators > 0:
            result['hinglish_confidence'] = min(1.0, total_indicators / 5)
        
        return result if total_indicators > 0 else None
    
    def batch_translate(self, texts: List[str], target_lang: str = 'en') -> List[str]:
        """
        Translate multiple texts efficiently.
        
        Args:
            texts: List of texts to translate
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        return [self.translate_text(text, target_lang=target_lang) for text in texts]
    
    def get_language_stats(self, messages: List[Dict]) -> Dict:
        """
        Generate language statistics from messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with language statistics
        """
        lang_stats = {}
        hinglish_count = 0
        
        for msg in messages:
            lang = msg.get('language', 'unknown')
            lang_stats[lang] = lang_stats.get(lang, 0) + 1
            
            # Check for Hinglish
            if lang == 'hi' and self.detect_hinglish(msg.get('text', '')):
                hinglish_count += 1
        
        return {
            'total_messages': len(messages),
            'language_distribution': lang_stats,
            'hinglish_messages': hinglish_count,
            'primary_language': max(lang_stats, key=lang_stats.get) if lang_stats else 'en',
            'language_diversity': len(lang_stats)
        }


# Singleton instance
_multilingual_service = None


def get_multilingual_service() -> MultilingualService:
    """Get or create multilingual service singleton."""
    global _multilingual_service
    if _multilingual_service is None:
        _multilingual_service = MultilingualService()
    return _multilingual_service
