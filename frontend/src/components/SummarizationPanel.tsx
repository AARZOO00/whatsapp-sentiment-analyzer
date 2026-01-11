import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SummarizationPanel.css';

const API_BASE = 'http://127.0.0.1:8000';

interface Summary {
  timestamp: string;
  message_count: number;
  short_summary?: string;
  detailed_summary?: string;
  key_topics?: string[];
  emotional_trend?: {
    windows: Array<{
      window: number;
      messages_count: number;
      positive: number;
      negative: number;
      trend: string;
    }>;
    overall_trend: string;
    total_messages: number;
  };
  available: boolean;
}

interface SummarizationPanelProps {
  jobId: string;
}

interface CollapsibleSectionProps {
  title: string;
  icon: string;
  children: React.ReactNode;
}

/**
 * Collapsible section component for better UX
 */
const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ title, icon, children }) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="summary-section collapsible-section">
      <div 
        className="section-header" 
        onClick={() => setIsOpen(!isOpen)}
        style={{ cursor: 'pointer', userSelect: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
      >
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          {icon} {title}
        </h3>
        <span style={{ fontSize: '1.2rem', transition: 'transform 0.2s' }}>
          {isOpen ? '▼' : '▶'}
        </span>
      </div>
      {isOpen && <div className="section-content">{children}</div>}
    </div>
  );
};

/**
 * Phase 3: Summarization Panel Component
 * Displays conversation summaries, topics, and emotional trends
 */
const SummarizationPanel: React.FC<SummarizationPanelProps> = ({ jobId }) => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (jobId) {
      fetchSummary();
    }
  }, [jobId]);

  const fetchSummary = async () => {
    if (!jobId) return;
    
    setLoading(true);
    setError(null);
    setRetrying(false);
    try {
      const response = await axios.post(`${API_BASE}/summarize/${jobId}`);
      console.log('Summary response:', response.data);
      
      // Handle both direct summary and nested analysis structure
      const summaryData = response.data?.analysis || response.data;
      
      // Ensure we have valid data before setting
      if (summaryData && (summaryData.short_summary || summaryData.detailed_summary || summaryData.key_topics)) {
        setSummary({ ...summaryData, available: true });
      } else {
        setError('Summary data is empty or incomplete');
        setSummary(null);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load summary';
      setError(String(errorMessage));
      setSummary(null);
      console.error('Summarization error:', errorMessage, err);
    } finally {
      setLoading(false);
    }
  };

  const retryFetch = async () => {
    setRetrying(true);
    await new Promise(r => setTimeout(r, 2000)); // Wait 2 seconds before retry
    await fetchSummary();
  };

  if (loading) {
    return <div className="summary-skeleton">Loading summary{retrying ? ' (retrying)' : ''}...</div>;
  }

  if (error) {
    return (
      <div className="summary-error">
        <p>❌ {error}</p>
        <button onClick={retryFetch} className="btn btn-primary mt-3">
          🔄 Retry
        </button>
      </div>
    );
  }

  if (!summary || !summary.available) {
    return (
      <div className="summary-empty">
        <p>⏳ Summarization not available yet. This may happen if:</p>
        <ul>
          <li>The job is still being processed</li>
          <li>Transformers library is not installed</li>
          <li>Job has not completed yet</li>
        </ul>
        <button onClick={fetchSummary} className="btn btn-primary mt-3">
          🔄 Check Again
        </button>
      </div>
    );
  }

  return (
    <div className="summarization-panel">
      {/* Short Summary */}
      {summary.short_summary && (
        <CollapsibleSection title="Quick Summary" icon="📝">
          <p className="summary-text">{summary.short_summary}</p>
        </CollapsibleSection>
      )}

      {/* Detailed Summary */}
      {summary.detailed_summary && (
        <CollapsibleSection title="Detailed Summary" icon="📚">
          <p className="summary-text">{summary.detailed_summary}</p>
        </CollapsibleSection>
      )}

      {/* Key Topics */}
      {summary.key_topics && summary.key_topics.length > 0 && (
        <CollapsibleSection title="Key Topics" icon="🏷️">
          <div className="topics-list">
            {summary.key_topics.map((topic, idx) => (
              <span key={idx} className="topic-badge">{topic}</span>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Emotional Trend */}
      {summary.emotional_trend && (
        <CollapsibleSection title="Emotional Trend" icon="📈">
          <p><strong>Overall Trend:</strong> {summary.emotional_trend.overall_trend}</p>
          <div className="trend-timeline">
            {summary.emotional_trend.windows.map((window) => (
              <div key={window.window} className={`trend-window trend-${window.trend}`}>
                <div className="window-number">W{window.window}</div>
                <div className="window-stats">
                  <span className="positive">+{window.positive}</span>
                  <span className="negative">-{window.negative}</span>
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      <button onClick={fetchSummary} className="refresh-btn">🔄 Refresh Summary</button>
    </div>
  );
};

export default SummarizationPanel;
