import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MediaViewer.css';

interface MediaItem {
  type: 'link' | 'image' | 'video' | 'document' | 'instagram' | 'youtube' | 'twitter';
  url: string;
  name?: string;
}

interface MessageWithMedia {
  id: string;
  sender: string;
  timestamp: string;
  text: string;
  media: MediaItem[];
}

const API_BASE = 'http://127.0.0.1:8000';

// URL extraction regexes
const URL_PATTERNS = {
  instagram: /(https?:\/\/(?:www\.)?instagram\.com\/[^\s]+)/gi,
  youtube: /(https?:\/\/(?:www\.|youtu\.)?(?:youtube\.com|youtu\.be)\/[^\s]+)/gi,
  twitter: /(https?:\/\/(?:www\.)?twitter\.com\/[^\s]+|https?:\/\/x\.com\/[^\s]+)/gi,
  image: /(https?:\/\/[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp))/gi,
  video: /(https?:\/\/[^\s]+\.(?:mp4|webm|mov|mkv|flv|avi))/gi,
  document: /(https?:\/\/[^\s]+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar))/gi,
  url: /(https?:\/\/[^\s]+)/gi,
};

/**
 * Media Viewer Component
 * Displays links, images, videos, and documents found in chat messages
 */
const MediaViewer: React.FC = () => {
  const [mediaMessages, setMediaMessages] = useState<MessageWithMedia[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');

  useEffect(() => {
    fetchMediaMessages();
  }, []);

  const extractMediaFromText = (text: string): MediaItem[] => {
    const media: MediaItem[] = [];
    const seenUrls = new Set<string>();

    // Check Instagram
    let match;
    URL_PATTERNS.instagram.lastIndex = 0;
    while ((match = URL_PATTERNS.instagram.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'instagram', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    // Check YouTube
    URL_PATTERNS.youtube.lastIndex = 0;
    while ((match = URL_PATTERNS.youtube.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'youtube', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    // Check Twitter/X
    URL_PATTERNS.twitter.lastIndex = 0;
    while ((match = URL_PATTERNS.twitter.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'twitter', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    // Check Images
    URL_PATTERNS.image.lastIndex = 0;
    while ((match = URL_PATTERNS.image.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'image', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    // Check Videos
    URL_PATTERNS.video.lastIndex = 0;
    while ((match = URL_PATTERNS.video.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'video', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    // Check Documents
    URL_PATTERNS.document.lastIndex = 0;
    while ((match = URL_PATTERNS.document.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'document', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    // Generic URLs (if not already matched)
    URL_PATTERNS.url.lastIndex = 0;
    while ((match = URL_PATTERNS.url.exec(text)) !== null) {
      if (!seenUrls.has(match[0])) {
        media.push({ type: 'link', url: match[0] });
        seenUrls.add(match[0]);
      }
    }

    return media;
  };

  const fetchMediaMessages = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all messages
      let allMessages: any[] = [];
      let page = 1;
      let hasMore = true;

      while (hasMore) {
        const response = await axios.get(`${API_BASE}/messages?limit=100&page=${page}`);
        const messages = response.data.messages || [];
        allMessages = allMessages.concat(messages);
        page++;
        hasMore = messages.length === 100;
      }

      // Extract media from messages
      const withMedia: MessageWithMedia[] = allMessages
        .map((msg: any) => ({
          id: msg.id,
          sender: msg.sender,
          timestamp: msg.timestamp,
          text: msg.text,
          media: extractMediaFromText(msg.text),
        }))
        .filter((msg) => msg.media.length > 0);

      setMediaMessages(withMedia);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load media';
      setError(String(errorMsg));
      console.error('Media fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMediaIcon = (type: string): string => {
    switch (type) {
      case 'instagram':
        return '📷';
      case 'youtube':
        return '▶️';
      case 'twitter':
        return '𝕏';
      case 'image':
        return '🖼️';
      case 'video':
        return '🎬';
      case 'document':
        return '📄';
      default:
        return '🔗';
    }
  };

  const getMediaLabel = (type: string): string => {
    switch (type) {
      case 'instagram':
        return 'Instagram';
      case 'youtube':
        return 'YouTube';
      case 'twitter':
        return 'Twitter/X';
      case 'image':
        return 'Image';
      case 'video':
        return 'Video';
      case 'document':
        return 'Document';
      default:
        return 'Link';
    }
  };

  const filteredMessages = selectedType === 'all'
    ? mediaMessages
    : mediaMessages.map(msg => ({
        ...msg,
        media: msg.media.filter(m => m.type === selectedType),
      })).filter(msg => msg.media.length > 0);

  const mediaStats = mediaMessages.reduce((acc, msg) => {
    msg.media.forEach(m => {
      acc[m.type] = (acc[m.type] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return <div className="media-viewer-skeleton">🔄 Loading media...</div>;
  }

  if (error) {
    return (
      <div className="media-viewer-error">
        <p>❌ {error}</p>
        <button onClick={fetchMediaMessages} className="btn btn-primary mt-3">
          🔄 Retry
        </button>
      </div>
    );
  }

  if (mediaMessages.length === 0) {
    return (
      <div className="media-viewer-empty">
        <p>📭 No media or links found in this conversation</p>
        <button onClick={fetchMediaMessages} className="btn btn-primary mt-3">
          🔄 Check Again
        </button>
      </div>
    );
  }

  return (
    <div className="media-viewer">
      <div className="media-viewer-header">
        <h2>🎨 Media & Links</h2>
        <p className="media-viewer-subtitle">
          {mediaMessages.length} messages with links and media content
        </p>
      </div>

      {/* Statistics */}
      <div className="media-stats">
        <button
          className={`stat-btn ${selectedType === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedType('all')}
        >
          All ({Object.values(mediaStats).reduce((a, b) => a + b, 0)})
        </button>
        {Object.entries(mediaStats)
          .sort((a, b) => b[1] - a[1])
          .map(([type, count]) => (
            <button
              key={type}
              className={`stat-btn ${selectedType === type ? 'active' : ''}`}
              onClick={() => setSelectedType(type)}
            >
              {getMediaIcon(type)} {getMediaLabel(type)} ({count})
            </button>
          ))}
      </div>

      {/* Messages */}
      <div className="media-messages">
        {filteredMessages.map((msg) => (
          <div key={msg.id} className="media-message-card">
            <div className="message-header">
              <strong>{msg.sender}</strong>
              <span className="timestamp">
                {new Date(msg.timestamp).toLocaleString()}
              </span>
            </div>
            <p className="message-text">{msg.text.substring(0, 150)}...</p>
            <div className="media-links">
              {msg.media.map((link, idx) => (
                <a
                  key={idx}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="media-link"
                  title={link.url}
                >
                  <span className="link-icon">{getMediaIcon(link.type)}</span>
                  <span className="link-text">{getMediaLabel(link.type)}</span>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="media-footer">
        <button onClick={fetchMediaMessages} className="btn btn-primary">
          🔄 Refresh
        </button>
      </div>
    </div>
  );
};

export default MediaViewer;
