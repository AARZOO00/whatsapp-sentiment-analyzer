import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './EmojiPanel.css';

interface EmojiData {
  emoji: string;
  count: number;
  percentage: number;
  senders: Set<string>;
}

const API_BASE = 'http://127.0.0.1:8000';

// Regex to extract emojis from text
const EMOJI_REGEX = /(\u{1F300}-\u{1F9FF}|[\u{2600}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{2300}-\u{23FF}]|[\u{2000}-\u{206F}]|[\u{2070}-\u{209F}]|[\u{20A0}-\u{20CF}]|[\u{2100}-\u{214F}]|[\u{2190}-\u{27FF}]|[\u{2900}-\u{297F}]|[\u{2B50}-\u{2BFF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E6}-\u{1F1FF}])/gu;

/**
 * Emoji Panel Component
 * Displays emoji usage statistics extracted from chat messages
 */
const EmojiPanel: React.FC = () => {
  const [emojiStats, setEmojiStats] = useState<EmojiData[]>([]);
  const [totalEmojis, setTotalEmojis] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEmojiStats();
  }, []);

  const extractEmojis = (text: string): string[] => {
    if (!text) return [];
    const matches = text.match(EMOJI_REGEX);
    return matches ? [...new Set(matches)] : [];
  };

  const fetchEmojiStats = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all messages to extract emoji data
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

      // Build emoji statistics
      const emojiMap = new Map<string, { count: number; senders: Set<string> }>();
      let totalCount = 0;

      allMessages.forEach((msg: any) => {
        // Extract emojis from message text
        const emojis = extractEmojis(msg.text);
        
        emojis.forEach((emoji: string) => {
          if (!emojiMap.has(emoji)) {
            emojiMap.set(emoji, { count: 0, senders: new Set() });
          }
          const data = emojiMap.get(emoji)!;
          data.count++;
          data.senders.add(msg.sender);
          totalCount++;
        });
      });

      // Convert to array and sort by count
      const stats: EmojiData[] = Array.from(emojiMap.entries())
        .map(([emoji, data]) => ({
          emoji,
          count: data.count,
          percentage: totalCount > 0 ? Math.round((data.count / totalCount) * 100 * 10) / 10 : 0,
          senders: data.senders,
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 50);

      setEmojiStats(stats);
      setTotalEmojis(totalCount);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load emoji statistics';
      setError(String(errorMsg));
      console.error('Emoji fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="emoji-panel-skeleton">📊 Loading emoji statistics...</div>;
  }

  if (error) {
    return (
      <div className="emoji-panel-error">
        <p>❌ {error}</p>
        <button onClick={fetchEmojiStats} className="btn btn-primary mt-3">
          🔄 Retry
        </button>
      </div>
    );
  }

  if (emojiStats.length === 0) {
    return (
      <div className="emoji-panel-empty">
        <p>😑 No emojis found in this conversation</p>
        <button onClick={fetchEmojiStats} className="btn btn-primary mt-3">
          🔄 Check Again
        </button>
      </div>
    );
  }

  return (
    <div className="emoji-panel">
      <div className="emoji-panel-header">
        <h2>😊 Emoji Analysis</h2>
        <p className="emoji-panel-subtitle">
          Top {emojiStats.length} emojis used in conversation • Total: {totalEmojis} emojis
        </p>
      </div>

      <div className="emoji-grid">
        {emojiStats.map((item, idx) => (
          <div key={idx} className="emoji-card">
            <div className="emoji-display">{item.emoji}</div>
            <div className="emoji-info">
              <div className="emoji-count">
                <strong>{item.count}</strong>
                <span className="count-label">uses</span>
              </div>
              <div className="emoji-percentage">
                <span>{item.percentage}%</span>
              </div>
              <div className="emoji-senders">
                <small>
                  <strong>Users:</strong> {item.senders.size}
                </small>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="emoji-panel-footer">
        <button onClick={fetchEmojiStats} className="btn btn-primary">
          🔄 Refresh
        </button>
      </div>
    </div>
  );
};

export default EmojiPanel;
