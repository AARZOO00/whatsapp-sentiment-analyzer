import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './ChatViewer.css';

// Reusable collapsible section component
interface CollapsibleSectionProps {
  title: string;
  icon: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ title, icon, children, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="collapsible-section">
      <div 
        className="section-header" 
        onClick={() => setIsOpen(!isOpen)}
        style={{ 
          cursor: 'pointer', 
          userSelect: 'none', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          padding: '12px',
          backgroundColor: '#f5f5f5',
          borderRadius: '6px',
          marginBottom: '12px',
          fontWeight: 'bold'
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {icon} {title}
        </span>
        <span style={{ fontSize: '1.2rem', transition: 'transform 0.2s' }}>
          {isOpen ? '▼' : '▶'}
        </span>
      </div>
      {isOpen && <div className="section-content">{children}</div>}
    </div>
  );
};

interface Message {
  id: string;
  timestamp: string;
  sender: string;
  text: string;
  translated_text?: string;
  language: string;
  ensemble_score: number;
  ensemble_label: 'Positive' | 'Negative' | 'Neutral';
  emotions?: Record<string, number>;
  keywords?: string[];
}

interface FilterState {
  startDate: string;
  endDate: string;
  selectedUser: string;
  sentiment: string;
  keyword: string;
}

interface MessagesResponse {
  messages: Message[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface StatsData {
  total_messages: number;
  sentiment_distribution: Record<string, any>;
  top_participants: Record<string, number>;
  language_distribution: Record<string, number>;
  average_sentiment_score: number;
}

const ChatViewer: React.FC = () => {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [users, setUsers] = useState<string[]>([]);

  // Filters
  const [filters, setFilters] = useState<FilterState>({
    startDate: '',
    endDate: '',
    selectedUser: '',
    sentiment: '',
    keyword: '',
  });

  const API_BASE = 'http://127.0.0.1:8000';
  const LIMIT = 25; // Messages per page

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.selectedUser) params.append('user', filters.selectedUser);

      const response = await axios.get<StatsData>(`${API_BASE}/stats?${params}`);
      setStats(response.data);

      // Extract user list from top_participants
      if (response.data.top_participants) {
        setUsers(Object.keys(response.data.top_participants));
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [filters]);

  // Fetch messages
  const fetchMessages = useCallback(async (page: number) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', LIMIT.toString());
      params.append('page', page.toString());

      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.selectedUser) params.append('user', filters.selectedUser);
      if (filters.sentiment) params.append('sentiment', filters.sentiment);
      if (filters.keyword) params.append('keyword', filters.keyword);

      const response = await axios.get<MessagesResponse>(
        `${API_BASE}/messages?${params}`
      );

      setMessages(response.data.messages);
      setTotalPages(response.data.total_pages);
      setCurrentPage(page);
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchMessages(1);
  }, [fetchStats, fetchMessages]);

  // Auto-refetch when filters change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (currentPage === 1) {
        fetchStats();
        fetchMessages(1);
      }
    }, 300); // Debounce by 300ms
    return () => clearTimeout(timer);
  }, [filters, currentPage, fetchStats, fetchMessages]);

  // Handle filter changes
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page on filter change
  };

  // Apply filters (kept for backward compatibility)
  const applyFilters = () => {
    fetchStats();
    fetchMessages(1);
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      selectedUser: '',
      sentiment: '',
      keyword: '',
    });
    setCurrentPage(1);
  };

  // Sentiment badge styling
  const getSentimentColor = (label: string) => {
    switch (label) {
      case 'Positive':
        return '#10b981'; // Green
      case 'Negative':
        return '#ef4444'; // Red
      default:
        return '#6b7280'; // Gray
    }
  };

  return (
    <div className="chat-viewer">
      {/* Header */}
      <div className="viewer-header">
        <h1>Chat Explorer</h1>
        <div className="header-stats">
          {stats && (
            <>
              <div className="stat-card">
                <span className="stat-label">Total Messages</span>
                <span className="stat-value">{stats.total_messages}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Avg Sentiment</span>
                <span className="stat-value">
                  {stats.average_sentiment_score.toFixed(2)}
                </span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Top User</span>
                <span className="stat-value">
                  {stats.top_participants
                    ? Object.entries(stats.top_participants)[0]?.[0] || 'N/A'
                    : 'N/A'}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <CollapsibleSection title="Filters" icon="🔍" defaultOpen={true}>
        <div className="filters-section">
          <div className="filter-grid">
            <div className="filter-group">
            <label htmlFor="startDate">Start Date</label>
            <input
              id="startDate"
              type="date"
              value={filters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="endDate">End Date</label>
            <input
              id="endDate"
              type="date"
              value={filters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="user">Participant</label>
            <select
              id="user"
              value={filters.selectedUser}
              onChange={(e) => handleFilterChange('selectedUser', e.target.value)}
            >
              <option value="">All Users</option>
              {users.map((user) => (
                <option key={user} value={user}>
                  {user}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="sentiment">Sentiment</label>
            <select
              id="sentiment"
              value={filters.sentiment}
              onChange={(e) => handleFilterChange('sentiment', e.target.value)}
            >
              <option value="">All</option>
              <option value="Positive">Positive</option>
              <option value="Neutral">Neutral</option>
              <option value="Negative">Negative</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="keyword">Keyword</label>
            <input
              id="keyword"
              type="text"
              placeholder="Search text..."
              value={filters.keyword}
              onChange={(e) => handleFilterChange('keyword', e.target.value)}
            />
          </div>

          <div className="filter-group button-group">
            <button className="btn btn-primary" onClick={applyFilters}>
              Apply Filters
            </button>
            <button className="btn btn-secondary" onClick={resetFilters}>
              Reset
            </button>
          </div>
        </div>
      </div>
      </CollapsibleSection>

      {/* Messages Table */}
      <CollapsibleSection title="Messages" icon="💬" defaultOpen={true}>
        {loading ? (
          <div className="loading">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="empty-state">
            <p>No messages found</p>
          </div>
        ) : (
          <>
            <div className="messages-table-wrapper">
              <table className="messages-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Sender</th>
                    <th>Message</th>
                    <th>Sentiment</th>
                    <th>Language</th>
                    <th>Score</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {messages.map((msg) => (
                    <tr key={msg.id} className="message-row">
                      <td className="col-timestamp">{msg.timestamp}</td>
                      <td className="col-sender">{msg.sender}</td>
                      <td className="col-text">{msg.text.substring(0, 50)}...</td>
                      <td className="col-sentiment">
                        <span
                          className="sentiment-badge"
                          style={{
                            backgroundColor: getSentimentColor(msg.ensemble_label),
                          }}
                        >
                          {msg.ensemble_label}
                        </span>
                      </td>
                      <td className="col-language">{msg.language}</td>
                      <td className="col-score">
                        {msg.ensemble_score.toFixed(2)}
                      </td>
                      <td className="col-action">
                        <button
                          className="btn btn-small"
                          onClick={() => {
                            setSelectedMessage(msg);
                            setShowDetailModal(true);
                          }}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <button
                disabled={currentPage === 1}
                onClick={() => fetchMessages(currentPage - 1)}
              >
                ← Previous
              </button>
              <span className="page-info">
                Page {currentPage} of {totalPages}
              </span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => fetchMessages(currentPage + 1)}
              >
                Next →
              </button>
            </div>
          </>
        )}
      </CollapsibleSection>

      {/* Message Detail Modal */}
      {showDetailModal && selectedMessage && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Message Detail</h2>
              <button className="close-btn" onClick={() => setShowDetailModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-row">
                <span className="label">Sender:</span>
                <span className="value">{selectedMessage.sender}</span>
              </div>
              <div className="detail-row">
                <span className="label">Timestamp:</span>
                <span className="value">{selectedMessage.timestamp}</span>
              </div>
              <div className="detail-row">
                <span className="label">Message:</span>
                <span className="value">{selectedMessage.text}</span>
              </div>
              {selectedMessage.translated_text && (
                <div className="detail-row">
                  <span className="label">Translation:</span>
                  <span className="value">{selectedMessage.translated_text}</span>
                </div>
              )}
              <div className="detail-row">
                <span className="label">Sentiment:</span>
                <span
                  className="sentiment-badge"
                  style={{
                    backgroundColor: getSentimentColor(selectedMessage.ensemble_label),
                  }}
                >
                  {selectedMessage.ensemble_label}
                </span>
              </div>
              <div className="detail-row">
                <span className="label">Score:</span>
                <span className="value">{selectedMessage.ensemble_score.toFixed(3)}</span>
              </div>
              <div className="detail-row">
                <span className="label">Language:</span>
                <span className="value">{selectedMessage.language}</span>
              </div>
              {selectedMessage.emotions && (
                <div className="detail-row">
                  <span className="label">Emotions:</span>
                  <div className="emotions">
                    {Object.entries(selectedMessage.emotions).map(([emotion, score]) => (
                      <div key={emotion} className="emotion-item">
                        {emotion}: {(score as number).toFixed(2)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedMessage.keywords && selectedMessage.keywords.length > 0 && (
                <div className="detail-row">
                  <span className="label">Keywords:</span>
                  <div className="keywords">
                    {selectedMessage.keywords.map((kw) => (
                      <span key={kw} className="keyword-tag">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatViewer;
