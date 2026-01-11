"""
Enterprise-Grade NLP Service for WhatsApp Chat Analysis
Provides parsing, sentiment analysis, emotions, keywords, and advanced NLP features
"""
import re
import emoji
import logging
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter
from backend.services.sentiment import sentiment_analyzer
from backend.services.language import detector, analytics, translate_text
from datetime import datetime

# Optional summarizer
HAS_SUMMARIZER = False
try:
    from transformers import pipeline
    HAS_SUMMARIZER = True
except Exception:
    HAS_SUMMARIZER = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatParser:
    """Parse WhatsApp chat exports from various formats."""
    
    # Regex to detect possible WhatsApp message start (many formats)
    # Examples matched: "8/15/24, 10:30 PM - Alice: msg", "2024-08-15, 21:30 - Alice: msg",
    # Also supports lines starting with [HH:MM] or dates with dashes/slashes.
    START_RE = re.compile(r"^(?P<date>\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\-]\d{1,2}[\-]\d{1,2}),?\s*(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APMapm]{2})?)\s*-\s*(?P<sender>[^:]+?):\s*(?P<message>.*)")
    
    @staticmethod
    def parse(content: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Parse WhatsApp chat content.
        
        Returns:
            (messages, failed_lines) - List of parsed messages and unparsed lines
        """
        lines = content.splitlines()
        messages = []
        failed_lines = []
        
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            # Try to match a message start (timestamp + sender)
            m = ChatParser.START_RE.match(line)
            if m:
                date_str = m.group('date')
                time_str = m.group('time')
                sender = m.group('sender').strip()
                msg_content = m.group('message').strip()

                # Normalize sender
                sender = ''.join(c for c in sender if c.isprintable()).strip()

                # Detect system messages
                if sender.lower() in ('system', 'you', 'group notification') or any(kw in msg_content.lower() for kw in ["secured", "created group", "changed", "left group", "added"]):
                    sender = 'System'

                # Try to parse timestamp to ISO if possible
                timestamp = f"{date_str}, {time_str}"
                iso_ts = timestamp
                try:
                    # Try several common formats
                    for fmt in ("%m/%d/%Y, %I:%M %p", "%m/%d/%y, %I:%M %p", "%d/%m/%Y, %H:%M", "%Y-%m-%d, %H:%M", "%m/%d/%Y, %H:%M"):
                        try:
                            dt = datetime.strptime(f"{date_str}, {time_str}", fmt)
                            iso_ts = dt.isoformat()
                            break
                        except Exception:
                            continue
                except Exception:
                    pass

                messages.append({
                    'timestamp': iso_ts,
                    'raw_timestamp': timestamp,
                    'sender': sender,
                    'message': msg_content
                })
            else:
                # Continuation of previous message if exists
                if messages:
                    messages[-1]['message'] += "\n" + line.strip()
                else:
                    failed_lines.append(line)
        
        return messages, failed_lines


class KeywordExtractor:
    """Extract important keywords from text."""
    
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that', 'the',
        'to', 'was', 'will', 'with', 'you', 'your', 'me', 'i', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'can', 'could'
    }
    
    @staticmethod
    def extract(text: str, top_k: int = 5) -> List[Tuple[str, int]]:
        """Extract top keywords from text."""
        if not text or not text.strip():
            return []
        
        try:
            # Remove URLs, emails, emojis
            clean = re.sub(r'http\S+|www\S+|\S+@\S+', '', text)
            clean = emoji.demojize(clean)
            
            # Extract words
            words = re.findall(r'\b\w+\b', clean.lower())
            
            # Filter stopwords and short words
            keywords = [w for w in words if w not in KeywordExtractor.STOP_WORDS and len(w) > 3]
            
            # Get top keywords
            counter = Counter(keywords)
            return counter.most_common(top_k)
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []


class MediaExtractor:
    """Extract media URLs and types from messages."""
    
    # URL regex patterns for common services
    MEDIA_PATTERNS = {
        'image': r'(https?://[^\s]+(?:\.jpg|\.jpeg|\.png|\.gif|\.webp|\.bmp))',
        'video': r'(https?://[^\s]+(?:\.mp4|\.avi|\.mov|\.mkv|\.webm))',
        'audio': r'(https?://[^\s]+(?:\.mp3|\.wav|\.m4a|\.flac|\.aac))',
        'document': r'(https?://[^\s]+(?:\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.ppt|\.pptx))',
        'general_url': r'(https?://[^\s]+)'
    }
    
    @staticmethod
    def extract(text: str) -> Dict[str, List[str]]:
        """
        Extract media URLs from message text.
        
        Returns:
            {
                'images': [...],
                'videos': [...],
                'audio': [...],
                'documents': [...],
                'links': [...]
            }
        """
        if not text or not text.strip():
            return {'images': [], 'videos': [], 'audio': [], 'documents': [], 'links': []}
        
        media = {'images': [], 'videos': [], 'audio': [], 'documents': [], 'links': []}
        
        try:
            # Check for media omitted indicator
            if '<Media omitted>' in text:
                media['media_omitted'] = True
                return media
            
            # Extract URLs by type
            for media_type, pattern in MediaExtractor.MEDIA_PATTERNS.items():
                if media_type == 'general_url':
                    continue  # Handle general URLs last
                matches = re.findall(pattern, text, re.IGNORECASE)
                if media_type in media and matches:
                    media[media_type] = list(set(matches))  # Remove duplicates
            
            # Extract remaining URLs (general links)
            all_urls = set()
            for matches in [re.findall(p, text, re.IGNORECASE) for p in MediaExtractor.MEDIA_PATTERNS.values()]:
                all_urls.update(matches)
            
            general_urls = re.findall(MediaExtractor.MEDIA_PATTERNS['general_url'], text)
            media['links'] = [url for url in general_urls if url not in all_urls]
            
        except Exception as e:
            logger.warning(f"Media extraction failed: {e}")
        
        return media


class EmotionDetector:
    """Detect emotions in text using heuristics."""
    
    EMOTIONS_MAP = {
        'joy': ['happy', 'glad', 'awesome', 'great', 'fantastic', 'love', 'excellent', '😊', '😄', '🎉'],
        'anger': ['angry', 'mad', 'furious', 'hate', 'terrible', 'worst', '😠', '🤬', '😤'],
        'sadness': ['sad', 'sorry', 'hurt', 'upset', 'down', 'depressed', '😢', '😭', '😔'],
        'fear': ['afraid', 'scared', 'worried', 'anxious', 'nervous', '😨', '😰', '😟'],
        'surprise': ['wow', 'amazing', 'shocking', 'unexpected', '😲', '🤯', '😯'],
    }
    
    @staticmethod
    def detect(text: str) -> Dict[str, float]:
        """
        Detect emotions in text.
        
        Returns:
            { 'joy': 0.8, 'anger': 0.0, ... } (normalized)
        """
        if not text or not text.strip():
            return {'joy': 0, 'anger': 0, 'sadness': 0, 'fear': 0, 'surprise': 0}
        
        text_lower = text.lower()
        emotions = {e: 0 for e in EmotionDetector.EMOTIONS_MAP.keys()}
        
        for emotion, keywords in EmotionDetector.EMOTIONS_MAP.items():
            emotion_count = sum(text_lower.count(kw) for kw in keywords)
            emotions[emotion] = emotion_count
        
        # Normalize
        total = sum(emotions.values())
        if total > 0:
            emotions = {e: (count / total) * 100 for e, count in emotions.items()}
        else:
            emotions = {e: 0 for e in emotions.keys()}
        
        return emotions


class NLPService:
    """Main NLP service orchestrating all analysis."""
    
    def __init__(self):
        """Initialize NLP service."""
        self.parser = ChatParser()
        self.sentiment = sentiment_analyzer
        self.emotions = EmotionDetector()
        self.keywords = KeywordExtractor()
        self.media = MediaExtractor()
        self.lang_detector = detector
        self.lang_analytics = analytics
        # Summarizer will be lazy-loaded when required to avoid heavy downloads at import time.
        self.summarizer = None
        logger.info("✓ NLP Service initialized")
    
    def analyze_chat(self, chat_content: str) -> Dict[str, Any]:
        """
        Analyze complete WhatsApp chat.
        
        Returns comprehensive analysis including sentiment, emotions, languages, etc.
        """
        try:
            # Parse chat
            messages, failed_lines = self.parser.parse(chat_content)
            
            if not messages:
                return {
                    'error': 'No valid messages found in chat file',
                    'total_messages': 0,
                    'failed_lines_count': len(failed_lines)
                }
            
            # Analyze each message
            analyzed_messages = []
            sentiments = []
            user_counts = Counter()
            emojis_list = []
            all_text = []
            
            for msg in messages:
                sender = msg.get('sender', '')
                text = msg.get('message', '')
                raw_ts = msg.get('raw_timestamp', '')
                ts = msg.get('timestamp', '')
                
                # Skip media-only messages
                if text == '<Media omitted>' or not text.strip():
                    continue
                
                # Sentiment (may include transformer results)
                sentiment = self.sentiment.analyze(text)
                sentiments.append(sentiment.get('ensemble_score', 0.0))

                # Emotions
                emotions = self.emotions.detect(text)

                # Language
                language = self.lang_detector.detect(text)

                # Translate if needed (preserve original)
                translated = text
                if language and language != 'en':
                    try:
                        translated = translate_text(text, target='en')
                    except Exception:
                        translated = text

                # Keywords (use translated for better English TF extraction)
                keywords = self.keywords.extract(translated or text, top_k=3)

                # Emojis
                msg_emojis = [e['emoji'] for e in emoji.emoji_list(text)]
                emojis_list.extend(msg_emojis)
                
                # Media URLs
                media_urls = self.media.extract(text)

                # Build structured message object
                analyzed_messages.append({
                    'timestamp': ts or raw_ts,
                    'raw_timestamp': raw_ts,
                    'sender': sender,
                    'message': text,
                    'translated_message': translated if translated != text else None,
                    'language': language,
                    'sentiment': {
                        'vader_score': sentiment.get('vader_score'),
                        'vader_label': sentiment.get('vader_label'),
                        'textblob_score': sentiment.get('textblob_score'),
                        'ensemble_score': sentiment.get('ensemble_score'),
                        'ensemble_label': sentiment.get('ensemble_label'),
                        'confidence': sentiment.get('confidence'),
                        'transformer_en': sentiment.get('transformer_en'),
                        'transformer_multi': sentiment.get('transformer_multi')
                    },
                    'emotions': emotions,
                    'keywords': keywords,
                    'emojis': msg_emojis,
                    'media': media_urls
                })
                
                user_counts[sender] += 1
                all_text.append(text)
            
            # Aggregations
            total_messages = len(analyzed_messages)
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Overall sentiment label
            if avg_sentiment >= 0.05:
                overall_label = 'Positive'
            elif avg_sentiment <= -0.05:
                overall_label = 'Negative'
            else:
                overall_label = 'Neutral'
            
            # Language distribution
            lang_analysis = self.lang_analytics.analyze_distribution(analyzed_messages)
            
            # Top users
            top_users = user_counts.most_common(5)
            
            # Top emojis
            top_emojis = Counter(emojis_list).most_common(10)
            
            # Aggregate emotions
            agg_emotions = {e: 0 for e in EmotionDetector.EMOTIONS_MAP.keys()}
            for msg in analyzed_messages:
                for emotion, score in msg['emotions'].items():
                    agg_emotions[emotion] += score
            
            if total_messages > 0:
                agg_emotions = {e: s / total_messages for e, s in agg_emotions.items()}
            
            logger.info(f"✓ Analyzed {total_messages} messages successfully")

            # Summarization (safe)
            summary_text = ''
            try:
                if HAS_SUMMARIZER and all_text:
                    # Lazy-load summarizer if available
                    if self.summarizer is None:
                        try:
                            from transformers import pipeline as _pipeline
                            self.summarizer = _pipeline('summarization')
                        except Exception as e:
                            logger.warning(f"Failed to initialize summarizer: {e}")
                            self.summarizer = None

                    if self.summarizer:
                        concat = '\n'.join(all_text[:200])
                        summ = self.summarizer(concat, max_length=150, min_length=40, do_sample=False)
                        summary_text = summ[0].get('summary_text', '') if isinstance(summ, list) and len(summ) > 0 else ''
                if not summary_text:
                    # Fallback: top keywords summarization
                    top_terms = Counter(' '.join(all_text).lower().split()).most_common(5)
                    summary_text = 'Summary topics: ' + ', '.join([t[0] for t in top_terms])
            except Exception as e:
                logger.warning(f"Summarization failed: {e}")
                summary_text = ''
            
            return {
                'total_messages': total_messages,
                'overall_sentiment': {
                    'ensemble_score': avg_sentiment,
                    'ensemble_label': overall_label,
                    'vader_score': avg_sentiment
                },
                'language_distribution': lang_analysis['distribution'],
                'primary_language': lang_analysis['primary_language'],
                'emotion_distribution': agg_emotions,
                'most_active_users': top_users,
                'top_emojis': top_emojis,
                'messages': analyzed_messages,
                'summary': summary_text or f"Analyzed {total_messages} messages with {overall_label} overall sentiment",
                'debug': {
                    'failed_lines': failed_lines[:10],
                    'parsed_messages': len(messages),
                }
            }
        
        except Exception as e:
            logger.error(f"Chat analysis failed: {e}", exc_info=True)
            return {'error': f'Analysis failed: {str(e)}'}


# Global instance
nlp_service = NLPService()
