"""
Language Detection and Translation Service
"""
import logging
from typing import Dict, Tuple
from langdetect import detect, LangDetectException
import asyncio
import inspect
from collections import defaultdict

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
    'ar': 'Arabic', 'hi': 'Hindi', 'bn': 'Bengali', 'pa': 'Punjabi',
    'te': 'Telugu', 'mr': 'Marathi', 'ta': 'Tamil', 'gu': 'Gujarati',
    'kn': 'Kannada', 'ml': 'Malayalam', 'tl': 'Tagalog', 'vi': 'Vietnamese',
    'th': 'Thai', 'id': 'Indonesian', 'my': 'Burmese', 'uk': 'Ukrainian',
    'pl': 'Polish', 'tr': 'Turkish', 'nl': 'Dutch', 'cs': 'Czech',
    'el': 'Greek', 'hu': 'Hungarian', 'ro': 'Romanian', 'sv': 'Swedish',
    'da': 'Danish', 'fi': 'Finnish', 'no': 'Norwegian', 'af': 'Afrikaans',
}


class LanguageDetector:
    """Detect language for text."""
    
    @staticmethod
    def detect(text: str) -> str:
        """
        Detect language of text.
        
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        if not text or not text.strip():
            return 'unknown'
        
        try:
            # Try langdetect
            lang_code = detect(text)
            return lang_code
        except LangDetectException:
            logger.warning(f"Could not detect language for text: {text[:50]}")
            return 'unknown'
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'unknown'
    
    @staticmethod
    def get_language_name(code: str) -> str:
        """Get language name from code."""
        return LANGUAGE_NAMES.get(code, code.upper())


def translate_text(text: str, target: str = 'en') -> str:
    """
    Translate text to target language if translation backend is available.
    Falls back to returning original text when no translator is available.
    """
    if not text or not text.strip():
        return text

    try:
        # try googletrans first (lightweight)
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=target)
        # Handle async translator implementations returning coroutines
        if inspect.isawaitable(result):
            try:
                result = asyncio.run(result)
            except RuntimeError:
                # If there's already a running event loop (e.g., in test runner), create a new loop
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(result)
                finally:
                    loop.close()

        return getattr(result, 'text', str(result))
    except Exception:
        # google-cloud-translate or other SDKs could be added here
        logger.debug("No translator available, returning original text")
        return text


class LanguageAnalytics:
    """Analyze language distribution in conversations."""
    
    @staticmethod
    def analyze_distribution(messages: list) -> Dict[str, any]:
        """
        Analyze language distribution.
        
        Args:
            messages: List of message dicts with 'message' field
            
        Returns:
            {
                'distribution': { 'en': 45.5, 'es': 32.2, ... },
                'languages_count': int,
                'primary_language': str,
                'language_pairs': { ('en', 'es'): 15, ... }
            }
        """
        lang_counts = defaultdict(int)
        language_sequence = []
        
        for msg in messages:
            text = msg.get('message', '')
            if text.strip():
                lang = LanguageDetector.detect(text)
                lang_counts[lang] += 1
                language_sequence.append(lang)
        
        total = sum(lang_counts.values())
        if total == 0:
            return {
                'distribution': {},
                'languages_count': 0,
                'primary_language': 'unknown',
                'language_pairs': {}
            }
        
        # Distribution percentages
        distribution = {
            lang: (count / total) * 100 
            for lang, count in lang_counts.items()
        }
        
        # Language pairs (consecutive messages)
        lang_pairs = defaultdict(int)
        for i in range(len(language_sequence) - 1):
            pair = tuple(sorted([language_sequence[i], language_sequence[i+1]]))
            lang_pairs[pair] += 1
        
        # Primary language
        primary = max(lang_counts, key=lang_counts.get) if lang_counts else 'unknown'
        
        return {
            'distribution': distribution,
            'languages_count': len(lang_counts),
            'primary_language': primary,
            'language_pairs': dict(lang_pairs)
        }


# Global instances
detector = LanguageDetector()
analytics = LanguageAnalytics()
