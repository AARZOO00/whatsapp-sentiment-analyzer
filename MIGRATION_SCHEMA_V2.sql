CREATE TABLE jobs_v2 (
    job_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,
    total_messages INTEGER DEFAULT 0,
    parsed_messages INTEGER DEFAULT 0,
    failed_messages INTEGER DEFAULT 0,
    overall_sentiment_score REAL DEFAULT 0.0,
    overall_sentiment_label TEXT DEFAULT 'Neutral',
    processing_time_seconds REAL DEFAULT 0.0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY(job_id) REFERENCES messages_v2(job_id) ON DELETE CASCADE
);

CREATE TABLE messages_v2 (
    message_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    sender TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT,
    translated_text TEXT,
    message_type TEXT DEFAULT 'text',
    is_media BOOLEAN DEFAULT 0,
    is_emoji_only BOOLEAN DEFAULT 0,
    is_link BOOLEAN DEFAULT 0,
    detected_language TEXT DEFAULT 'en',
    language_confidence REAL DEFAULT 0.0,
    vader_score REAL DEFAULT 0.0,
    vader_label TEXT DEFAULT 'Neutral',
    textblob_score REAL DEFAULT 0.0,
    textblob_label TEXT DEFAULT 'Neutral',
    ensemble_score REAL DEFAULT 0.0,
    ensemble_label TEXT DEFAULT 'Neutral',
    confidence_score REAL DEFAULT 0.0,
    emotions TEXT,
    top_emotion TEXT,
    keywords TEXT,
    emoji_list TEXT,
    media_types TEXT,
    media_count INTEGER DEFAULT 0,
    toxicity_score REAL DEFAULT 0.0,
    is_toxic BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs_v2(job_id) ON DELETE CASCADE
);

CREATE TABLE emoji_analytics (
    emoji_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    emoji_char TEXT NOT NULL,
    emoji_name TEXT,
    emoji_category TEXT,
    usage_count INTEGER DEFAULT 1,
    unique_users INTEGER DEFAULT 1,
    user_list TEXT,
    first_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs_v2(job_id) ON DELETE CASCADE,
    UNIQUE(job_id, emoji_char)
);

CREATE TABLE emoji_senders (
    emoji_sender_id TEXT PRIMARY KEY,
    emoji_id TEXT NOT NULL,
    sender_name TEXT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    FOREIGN KEY(emoji_id) REFERENCES emoji_analytics(emoji_id) ON DELETE CASCADE
);

CREATE TABLE media_analytics (
    media_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    media_type TEXT NOT NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs_v2(job_id) ON DELETE CASCADE,
    FOREIGN KEY(message_id) REFERENCES messages_v2(message_id) ON DELETE CASCADE
);

CREATE TABLE summaries (
    summary_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    short_summary TEXT,
    detailed_summary TEXT,
    key_topics TEXT,
    emotional_trend TEXT,
    sentiment_timeline TEXT,
    top_keywords TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs_v2(job_id) ON DELETE CASCADE
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_messages_job_id ON messages_v2(job_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages_v2(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages_v2(sender);
CREATE INDEX IF NOT EXISTS idx_messages_sentiment ON messages_v2(ensemble_label);
CREATE INDEX IF NOT EXISTS idx_messages_language ON messages_v2(detected_language);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages_v2(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_toxic ON messages_v2(is_toxic);

CREATE INDEX IF NOT EXISTS idx_emoji_job_id ON emoji_analytics(job_id);
CREATE INDEX IF NOT EXISTS idx_emoji_char ON emoji_analytics(emoji_char);

CREATE INDEX IF NOT EXISTS idx_media_job_id ON media_analytics(job_id);
CREATE INDEX IF NOT EXISTS idx_media_type ON media_analytics(media_type);

CREATE INDEX IF NOT EXISTS idx_summaries_job_id ON summaries(job_id);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs_v2(status);
