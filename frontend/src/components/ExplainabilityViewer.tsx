import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ExplainabilityViewer.css';

const API_BASE = 'http://127.0.0.1:8000';

interface ModelAnalysis {
  score: number;
  confidence: number;
  label: string;
  explanation: string;
}

interface Explanation {
  message_id: string;
  text_preview: string;
  per_model_analysis: {
    vader: ModelAnalysis;
    textblob: ModelAnalysis;
    ensemble: ModelAnalysis;
  };
  disagreement?: {
    disagreement: boolean;
    vader_says: string;
    textblob_says: string;
    possible_reason: string;
    recommendation: string;
  };
  confidence_metrics: {
    model_agreement_score: number;
    overall_confidence_level: string;
    vader_confidence: number;
    textblob_confidence: number;
    ensemble_confidence: number;
    recommendation: string;
  };
  important_words: {
    positive_indicators: string[];
    negative_indicators: string[];
  };
  final_verdict: {
    sentiment: string;
    score: number;
    confidence: number;
  };
}

interface Message {
  id: string;
  sender: string;
  text: string;
  timestamp: string;
}

/**
 * Phase 5: Explainability Viewer Component
 * Shows per-model analysis, confidence metrics, and explanations
 */
const ExplainabilityViewer: React.FC = () => {
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [availableMessages, setAvailableMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [selectedMessageId, setSelectedMessageId] = useState('');
  const [showMessageList, setShowMessageList] = useState(true);

  // Load available messages on mount
  useEffect(() => {
    fetchAvailableMessages();
  }, []);

  const fetchAvailableMessages = async () => {
    setLoadingMessages(true);
    try {
      const response = await axios.get(`${API_BASE}/messages?limit=100`);
      setAvailableMessages(response.data.messages || []);
    } catch (err: any) {
      console.error('Failed to load messages:', err);
      setError('Failed to load messages');
    } finally {
      setLoadingMessages(false);
    }
  };

  const fetchExplanation = async (messageId: string) => {
    if (!messageId) {
      setError('Please select a message');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/explain/${messageId}`);
      setExplanation(response.data);
      setShowMessageList(false);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to load explanation. Message may not have analysis yet.';
      setError(errorMsg);
      setExplanation(null);
      console.error('Explanation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMessageSelect = (messageId: string) => {
    setSelectedMessageId(messageId);
    fetchExplanation(messageId);
  };

  const filteredMessages = availableMessages.filter(msg =>
    msg.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    msg.sender.toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 50);

  if (explanation && !showMessageList) {
    return (
      <div className="explainability-viewer">
        <div className="explanation-header">
          <h2>📊 Message Analysis</h2>
          <p className="message-preview">"{explanation.text_preview.substring(0, 100)}..."</p>
          <button onClick={() => { setExplanation(null); setShowMessageList(true); }} className="back-btn">← Back to Messages</button>
        </div>

        {/* Final Verdict */}
        <div className={`verdict-box verdict-${explanation.final_verdict.sentiment.toLowerCase()}`}>
          <h3>Final Verdict</h3>
          <div className="verdict-content">
            <div className="verdict-label">{explanation.final_verdict.sentiment}</div>
            <div className="verdict-score">Score: {explanation.final_verdict.score.toFixed(3)}</div>
            <div className="verdict-confidence">Confidence: {(explanation.final_verdict.confidence * 100).toFixed(1)}%</div>
          </div>
        </div>

        {/* Per-Model Analysis */}
        <div className="analysis-grid">
          <div className="model-card vader-card">
            <h3>VADER</h3>
            <div className="score-display">
              <span className="score-value">{explanation.per_model_analysis.vader.score.toFixed(3)}</span>
              <span className="score-label">{explanation.per_model_analysis.vader.label}</span>
            </div>
            <div className="confidence-bar">
              <div style={{ width: `${explanation.per_model_analysis.vader.confidence * 100}%` }} className="confidence-fill"></div>
            </div>
            <p className="model-explanation">{explanation.per_model_analysis.vader.explanation}</p>
            <small className="model-type">Lexicon-based approach</small>
          </div>

          <div className="model-card textblob-card">
            <h3>TextBlob</h3>
            <div className="score-display">
              <span className="score-value">{explanation.per_model_analysis.textblob.score.toFixed(3)}</span>
              <span className="score-label">{explanation.per_model_analysis.textblob.label}</span>
            </div>
            <div className="confidence-bar">
              <div style={{ width: `${explanation.per_model_analysis.textblob.confidence * 100}%` }} className="confidence-fill"></div>
            </div>
            <p className="model-explanation">{explanation.per_model_analysis.textblob.explanation}</p>
            <small className="model-type">Polarity & subjectivity</small>
          </div>

          <div className="model-card ensemble-card">
            <h3>Ensemble</h3>
            <div className="score-display">
              <span className="score-value">{explanation.per_model_analysis.ensemble.score.toFixed(3)}</span>
              <span className="score-label">{explanation.per_model_analysis.ensemble.label}</span>
            </div>
            <div className="confidence-bar">
              <div style={{ width: `${explanation.per_model_analysis.ensemble.confidence * 100}%` }} className="confidence-fill"></div>
            </div>
            <p className="model-explanation">{explanation.per_model_analysis.ensemble.explanation}</p>
            <small className="model-type">VADER 60% + TextBlob 40%</small>
          </div>
        </div>

        {/* Important Words */}
        <div className="important-words-section">
          <h3>🔑 Contributing Words</h3>
          <div className="words-grid">
            <div className="words-column">
              <h4 className="positive-label">Positive Indicators</h4>
              <div className="words-list">
                {explanation.important_words.positive_indicators.length > 0 ? (
                  explanation.important_words.positive_indicators.map((word, idx) => (
                    <span key={idx} className="word-badge positive">{word}</span>
                  ))
                ) : (
                  <p className="empty-state">No positive indicators</p>
                )}
              </div>
            </div>
            <div className="words-column">
              <h4 className="negative-label">Negative Indicators</h4>
              <div className="words-list">
                {explanation.important_words.negative_indicators.length > 0 ? (
                  explanation.important_words.negative_indicators.map((word, idx) => (
                    <span key={idx} className="word-badge negative">{word}</span>
                  ))
                ) : (
                  <p className="empty-state">No negative indicators</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show message selection
  return (
    <div className="explainability-viewer">
      <div className="search-box">
        <h2>🔍 Message Explainability</h2>
        <p className="search-subtitle">Select a message to see detailed sentiment analysis</p>
        <div className="search-input-group">
          <input
            type="text"
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button onClick={fetchAvailableMessages} className="refresh-btn" disabled={loadingMessages}>
            🔄 Refresh
          </button>
        </div>
        {error && <div className="error-message">❌ {error}</div>}
      </div>

      {loadingMessages ? (
        <div className="loading-state">Loading messages...</div>
      ) : filteredMessages.length === 0 ? (
        <div className="empty-state">
          {availableMessages.length === 0 
            ? '📭 No messages found. Upload a chat file first.' 
            : '🔍 No matching messages.'}
        </div>
      ) : (
        <div className="messages-list">
          {filteredMessages.map((msg, idx) => (
            <div key={idx} className="message-item">
              <div className="message-item-header">
                <strong>{msg.sender}</strong>
                <small>{new Date(msg.timestamp).toLocaleString()}</small>
              </div>
              <p className="message-text">{msg.text.substring(0, 150)}{msg.text.length > 150 ? '...' : ''}</p>
              <button 
                className="analyze-btn"
                onClick={() => handleMessageSelect(msg.id)}
                disabled={loading && selectedMessageId === msg.id}
              >
                {loading && selectedMessageId === msg.id ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExplainabilityViewer;
