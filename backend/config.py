from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ML model settings
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    EMOTION_MODEL: str = "j-hartmann/emotion-english-distilroberta-base"
    TOXICITY_MODEL: str = "unitary/toxic-bert"
    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    TRANSLATION_MODEL_PREFIX: str = "Helsinki-NLP/opus-mt-"

    # Analysis thresholds and counts
    VADER_POSITIVE_THRESHOLD: float = 0.05
    VADER_NEGATIVE_THRESHOLD: float = -0.05
    TOP_USERS_COUNT: int = 5
    TOP_EMOJIS_COUNT: int = 10
    MAX_SAMPLE_FAILED_LINES: int = 5

    # Caching settings
    CACHE_SIZE: int = 128

    class Config:
        env_file = ".env"

settings = Settings()