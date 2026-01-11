import React, { useState, useEffect } from 'react';
import { startAnalysisApi, getResultsApi } from './api';
import FileUpload from './components/FileUpload';
import Dashboard from './components/Dashboard';
import ChatViewer from './components/ChatViewer';
import SummarizationPanel from './components/SummarizationPanel';
import ExplainabilityViewer from './components/ExplainabilityViewer';
import EmojiPanel from './components/EmojiPanel';
import MediaViewer from './components/MediaViewer';

// Define the shape of the analysis data from the backend
export interface AnalysisData {
  total_messages: number;
  summary: string;
  overall_sentiment: {
    ensemble_score: number;
    ensemble_label: string;
    vader_score: number;
  };
  language_distribution: { [key: string]: number };
  primary_language: string;
  emotion_distribution: { [key: string]: number };
  most_active_users: [string, number][];
  top_emojis: [string, number][];
  messages: Array<{
    timestamp?: string;
    raw_timestamp?: string;
    sender: string;
    message: string;
    translated_message?: string | null;
    language: string;
    sentiment: {
      vader_score?: number;
      vader_label?: string;
      textblob_score?: number;
      ensemble_score?: number;
      ensemble_label?: string;
      confidence?: number;
      transformer_en?: any;
      transformer_multi?: any;
    };
    emotions: { [key: string]: number };
    keywords: [string, number][];
    emojis: string[];
  }>;
}

// Define the shape of the error object
interface ErrorInfo {
  message: string;
  debug_info?: {
    total_lines_read: number;
    matched_lines: number;
    sample_failed_lines: string[];
  };
}

const App: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<ErrorInfo | string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [activeTab, setActiveTab] = useState<'upload' | 'viewer' | 'summarize' | 'explain' | 'emoji' | 'media'>('upload');

  useEffect(() => {
    if (jobId && isPolling) {
      const pollInterval = setInterval(async () => {
        try {
          const response = await getResultsApi(jobId);
          if (response.status === 'complete') {
            clearInterval(pollInterval);
            setIsPolling(false);
            setAnalysisData(response.result);
          } else if (response.status === 'processing') {
            // Still processing, do nothing
          }
        } catch (err: any) {
          clearInterval(pollInterval);
          setIsPolling(false);
          const errorDetail = err.response?.data?.detail;
          if (typeof errorDetail === 'object' && errorDetail !== null) {
            setError(errorDetail as ErrorInfo);
          } else {
            setError(errorDetail || 'An unexpected error occurred during polling.');
          }
        }
      }, 3000); // Poll every 3 seconds

      return () => clearInterval(pollInterval);
    }
  }, [jobId, isPolling]);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setAnalysisData(null);
    setJobId(null);
    setIsPolling(false);

    try {
      const response = await startAnalysisApi(file);
      setJobId(response.job_id);
      setIsPolling(true);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      if (typeof errorDetail === 'object' && errorDetail !== null) {
        setError(errorDetail as ErrorInfo);
      } else {
        setError(errorDetail || 'An unexpected error occurred during file upload.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
    document.body.classList.toggle('dark-mode');
  };

  const renderError = () => {
    if (!error) return null;

    if (typeof error === 'string') {
      return (
        <div className="alert alert-danger mt-4 p-4 rounded-3" role="alert" style={{ borderLeft: '5px solid #dc3545' }}>
          <div className="d-flex align-items-center mb-2">
            <span style={{ fontSize: '1.5rem', marginRight: '10px' }}>⚠️</span>
            <strong style={{ fontSize: '1.1rem' }}>Analysis Failed</strong>
          </div>
          <p className="mb-0" style={{ fontSize: '0.95rem' }}>{error}</p>
          <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(220, 53, 69, 0.3)' }}>
            <small className="text-muted">
              💡 <strong>Try this:</strong> Make sure the file is a WhatsApp chat export (not media), saved as .txt format, and UTF-8 encoded.
            </small>
          </div>
        </div>
      );
    }

    return (
      <div className="alert alert-warning mt-4 p-4 rounded-3" role="alert" style={{ borderLeft: '5px solid #ffc107' }}>
        <h4 className="alert-heading d-flex align-items-center mb-3">
          <span style={{ fontSize: '1.5rem', marginRight: '10px' }}>🔍</span>
          Chat Format Issue
        </h4>
        <p style={{ marginBottom: '1rem' }}><strong>{error.message}</strong></p>
        {error.debug_info && (
          <>
            <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.5)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <p className="mb-2"><strong>📊 Analysis Details:</strong></p>
              <ul style={{ marginBottom: 0 }}>
                <li>Total lines read: <strong>{error.debug_info.total_lines_read}</strong></li>
                <li>Successfully parsed: <strong>{error.debug_info.matched_lines}</strong> messages</li>
                {error.debug_info.sample_failed_lines.length > 0 && (
                  <li>
                    <strong>Unparseable lines (first 5):</strong>
                    <pre className="bg-dark text-light p-3 rounded mt-2 overflow-auto" style={{ maxHeight: '200px', fontSize: '0.85rem' }}>
                      <code>{error.debug_info.sample_failed_lines.slice(0, 5).join('\n')}</code>
                    </pre>
                  </li>
                )}
              </ul>
            </div>
            <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.5)', padding: '1rem', borderRadius: '8px' }}>
              <p className="mb-2"><strong>💡 Suggestions:</strong></p>
              <ul style={{ marginBottom: 0, fontSize: '0.9rem' }}>
                <li>Ensure you exported without media/attachments</li>
                <li>Check the date format matches WhatsApp exports (usually MM/DD/YYYY HH:MM)</li>
                <li>Try exporting from WhatsApp again with the correct settings</li>
                <li>Make sure file encoding is UTF-8</li>
              </ul>
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className={`app-container theme-${theme}`}>
      <nav className="navbar navbar-expand-lg shadow-lg sticky-top">
        <div className="container-fluid px-4">
          <a className="navbar-brand" href="#">
            <span style={{ fontSize: '1.8rem', fontWeight: 'bold' }}>💧 WhatsApp Analyzer</span>
          </a>
          <button className="btn btn-outline-secondary ms-auto" onClick={toggleTheme}>
            {theme === 'light' ? '🌙 Dark' : '☀️ Light'}
          </button>
        </div>
      </nav>

      <div className="container-fluid" style={{ padding: '2rem 3rem' }}>
        <header className="text-center mb-5" style={{ paddingTop: '1rem' }}>
          <h1 className="display-3" style={{ marginBottom: '1rem' }}>💬 Chat Analytics Hub</h1>
          <p className="lead fs-5">
            Discover emotional patterns and insights from your WhatsApp conversations with AI-powered analysis.
          </p>
        </header>

        {/* Tab Navigation */}
        <div className="nav nav-tabs mb-4" role="tablist" style={{ borderBottom: '2px solid #e0e0e0' }}>
          <button
            className={`nav-link ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
            style={{
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              padding: '12px 20px',
              fontWeight: activeTab === 'upload' ? 'bold' : 'normal',
              color: activeTab === 'upload' ? '#00897b' : '#666',
              borderBottom: activeTab === 'upload' ? '3px solid #00897b' : 'none',
              marginRight: '10px',
            }}
          >
            📊 Analysis
          </button>
          <button
            className={`nav-link ${activeTab === 'viewer' ? 'active' : ''}`}
            onClick={() => setActiveTab('viewer')}
            style={{
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              padding: '12px 20px',
              fontWeight: activeTab === 'viewer' ? 'bold' : 'normal',
              color: activeTab === 'viewer' ? '#00897b' : '#666',
              borderBottom: activeTab === 'viewer' ? '3px solid #00897b' : 'none',
              marginRight: '10px',
            }}
          >
            💬 Chat Explorer
          </button>
          <button
            className={`nav-link ${activeTab === 'summarize' ? 'active' : ''}`}
            onClick={() => setActiveTab('summarize')}
            style={{
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              padding: '12px 20px',
              fontWeight: activeTab === 'summarize' ? 'bold' : 'normal',
              color: activeTab === 'summarize' ? '#00897b' : '#666',
              borderBottom: activeTab === 'summarize' ? '3px solid #00897b' : 'none',
              marginRight: '10px',
            }}
          >
            📝 Summarization
          </button>
          <button
            className={`nav-link ${activeTab === 'explain' ? 'active' : ''}`}
            onClick={() => setActiveTab('explain')}
            style={{
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              padding: '12px 20px',
              fontWeight: activeTab === 'explain' ? 'bold' : 'normal',
              color: activeTab === 'explain' ? '#00897b' : '#666',
              borderBottom: activeTab === 'explain' ? '3px solid #00897b' : 'none',
              marginRight: '10px',
            }}
          >
            🔍 Explainability
          </button>
          <button
            className={`nav-link ${activeTab === 'emoji' ? 'active' : ''}`}
            onClick={() => setActiveTab('emoji')}
            style={{
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              padding: '12px 20px',
              fontWeight: activeTab === 'emoji' ? 'bold' : 'normal',
              color: activeTab === 'emoji' ? '#00897b' : '#666',
              borderBottom: activeTab === 'emoji' ? '3px solid #00897b' : 'none',
              marginRight: '10px',
            }}
          >
            😊 Emojis
          </button>
          <button
            className={`nav-link ${activeTab === 'media' ? 'active' : ''}`}
            onClick={() => setActiveTab('media')}
            style={{
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              padding: '12px 20px',
              fontWeight: activeTab === 'media' ? 'bold' : 'normal',
              color: activeTab === 'media' ? '#00897b' : '#666',
              borderBottom: activeTab === 'media' ? '3px solid #00897b' : 'none',
            }}
          >
            🎨 Media
          </button>
        </div>

        <main>
          {/* Analysis Tab */}
          {activeTab === 'upload' && (
            <>
              {!analysisData && !isLoading && !isPolling && (
                <div className="row justify-content-center">
                  <div className="col-lg-8">
                    <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading || isPolling} error={typeof error === 'string' ? error : null} />
                  </div>
                </div>
              )}

              {(isLoading || isPolling) && (
                <div className="spinner-container">
                  <div className="spinner-border" role="status" style={{ width: '4rem', height: '4rem', color: '#00897b' }}>
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className="mt-4 fs-5" style={{ color: '#00695c', fontWeight: 600 }}>
                    {isPolling ? '✨ Analyzing your chat...' : '📤 Uploading file...'}
                  </p>
                </div>
              )}

              {error && (
                <div className="row justify-content-center">
                  <div className="col-lg-8">
                    {renderError()}
                    <button 
                      onClick={() => { setError(null); setAnalysisData(null); setJobId(null); setIsPolling(false); }} 
                      className="btn btn-primary mt-3 px-4 py-2"
                    >
                      ↻ Try Again
                    </button>
                  </div>
                </div>
              )}

              {analysisData && (
                <Dashboard data={analysisData} />
              )}
            </>
          )}

          {/* Chat Explorer Tab */}
          {activeTab === 'viewer' && (
            <ChatViewer />
          )}

          {/* Summarization Tab */}
          {activeTab === 'summarize' && (
            jobId ? (
              <SummarizationPanel jobId={jobId} />
            ) : (
              <div className="alert alert-info" role="alert">
                <strong>📝 Summarization:</strong> Please complete an analysis first to see summaries, topics, and emotional trends.
              </div>
            )
          )}

          {/* Explainability Tab */}
          {activeTab === 'explain' && (
            <ExplainabilityViewer />
          )}

          {/* Emoji Tab */}
          {activeTab === 'emoji' && (
            <EmojiPanel />
          )}

          {/* Media Tab */}
          {activeTab === 'media' && (
            <MediaViewer />
          )}
        </main>
        
        <footer className="text-center mt-5 py-4" style={{ color: '#00695c', fontWeight: 500 }}>
          <p>✨ Advanced AI-Powered Chat Analytics | Powered by FastAPI, React & HuggingFace</p>
        </footer>
      </div>
    </div>
  );
};

export default App;