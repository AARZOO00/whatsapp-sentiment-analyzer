import React, { useState } from 'react'; // Import useState
import StatCard from './StatCard';
import UserChart from './UserChart';
import EmojiList from './EmojiList';
import EmotionChart from './EmotionChart';
import LanguageDistributionChart from './LanguageDistributionChart';
import type { AnalysisData } from '../App'; // Import type from App.tsx
import Papa from 'papaparse'; // Import PapaParse

interface DashboardProps {
  data: AnalysisData;
}

const Dashboard: React.FC<DashboardProps> = ({ data }) => {
  // State for filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedParticipant, setSelectedParticipant] = useState('');
  const [filteredMessages, setFilteredMessages] = useState(data.messages);

  // Extract unique participants for the filter dropdown
  const participants = Array.from(new Set(data.messages.map(msg => msg.sender)));

  // Helper to parse timestamps robustly
  const parseTimestamp = (ts?: string, raw?: string) => {
    const t = ts || raw || '';
    const d = new Date(t);
    if (!isNaN(d.getTime())) return d;
    // Try replace common separators
    try {
      const replaced = t.replace(/,/, '').replace(/-/g, '/');
      const d2 = new Date(replaced);
      if (!isNaN(d2.getTime())) return d2;
    } catch (e) {
      // ignore
    }
    return null;
  };

  // Compute derived datasets from filteredMessages
  const computeUserChart = () => {
    const counts: { [k: string]: number } = {};
    (filteredMessages || data.messages).forEach(m => {
      counts[m.sender] = (counts[m.sender] || 0) + 1;
    });
    return Object.entries(counts).map(([name, cnt]) => ({ name, messages: cnt }));
  };

  const computeEmotionChart = () => {
    const agg: { [k: string]: number } = {};
    (filteredMessages || data.messages).forEach(m => {
      Object.entries(m.emotions || {}).forEach(([k, v]) => {
        agg[k] = (agg[k] || 0) + (v || 0);
      });
    });
    return Object.entries(agg).map(([name, value]) => ({ name, value }));
  };

  const computeLanguageChart = () => {
    const counts: { [k: string]: number } = {};
    (filteredMessages || data.messages).forEach(m => {
      counts[m.language] = (counts[m.language] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  };

  const userChartData = computeUserChart();
  const emotionChartData = computeEmotionChart();
  const languageChartData = computeLanguageChart();

  const overallSentimentEmoji: { [key: string]: string } = { // Explicitly define index signature
    'Positive': '😊',
    'Negative': '😠',
    'Neutral': '😐'
  };

  const applyFilters = () => {
    const s = startDate ? new Date(startDate) : null;
    const e = endDate ? new Date(endDate) : null;

    const filtered = data.messages.filter(msg => {
      // participant filter
      if (selectedParticipant && msg.sender !== selectedParticipant) return false;

      // date filter
      const d = parseTimestamp(msg.timestamp, msg.raw_timestamp);
      if (d) {
        if (s && d < s) return false;
        if (e) {
          // ensure endDate includes entire day
          const endOfDay = new Date(e.getTime());
          endOfDay.setHours(23,59,59,999);
          if (d > endOfDay) return false;
        }
      }

      return true;
    });

    setFilteredMessages(filtered);
  };

  const exportToCsv = () => {
    const messagesForExport = (filteredMessages || data.messages).map(msg => ({
      timestamp: msg.timestamp || msg.raw_timestamp || '',
      sender: msg.sender,
      message: msg.message,
      translated_message: msg.translated_message || '',
      language: msg.language,
      vader_score: msg.sentiment.vader_score,
      vader_label: msg.sentiment.vader_label,
      textblob_score: msg.sentiment.textblob_score,
      ensemble_score: msg.sentiment.ensemble_score,
      ensemble_label: msg.sentiment.ensemble_label,
      transformer_en: JSON.stringify(msg.sentiment.transformer_en || ''),
      transformer_multi: JSON.stringify(msg.sentiment.transformer_multi || ''),
      emotions: JSON.stringify(msg.emotions),
      keywords: JSON.stringify(msg.keywords),
    }));

    const csv = Papa.unparse(messagesForExport);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'whatsapp_chat_analysis.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToPdf = () => {
    // Simple PDF export approach: open printable summary window
    const html = `
      <html>
      <head>
        <title>Chat Analysis Report</title>
        <style>body{font-family: Arial, sans-serif; padding:20px;}</style>
      </head>
      <body>
        <h1>Chat Analysis Report</h1>
        <h3>Summary</h3>
        <p>${data.summary}</p>
        <h3>KPIs</h3>
        <ul>
          <li>Total Messages: ${data.total_messages}</li>
          <li>Overall Sentiment: ${data.overall_sentiment.ensemble_label} (${data.overall_sentiment.ensemble_score.toFixed(3)})</li>
          <li>Primary Language: ${data.primary_language}</li>
        </ul>
        <h3>Top Messages (filtered)</h3>
        <pre>${(filteredMessages || data.messages).slice(0,50).map(m=>`${m.timestamp||m.raw_timestamp} | ${m.sender}: ${m.message}`).join('\n\n')}</pre>
      </body>
      </html>
    `;

    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(html);
    w.document.close();
    w.print();
  };


  return (
    <div className="container-fluid">
      {/* Summary */}
      <div className="card shadow-sm border-0 rounded-4 mb-5" style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
        borderLeft: '5px solid #0097a7'
      }}>
        <div className="card-body p-4">
          <h5 className="card-title mb-3" style={{ color: '#00695c', fontSize: '1.2rem', fontWeight: 700 }}>
            ✨ AI Chat Summary
          </h5>
          <p className="card-text" style={{ color: '#00897b', lineHeight: '1.8', fontSize: '1rem' }}>
            {data.summary}
          </p>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="row g-4 mb-5">
        <div className="col-lg-3 col-md-6">
          <StatCard title="Total Messages" value={(filteredMessages || data.messages).length} icon="💬" />
        </div>
        <div className="col-lg-3 col-md-6">
          <StatCard 
            title="Overall Sentiment" 
            value={(() => {
              // compute simple average of ensemble_score over filtered messages
              const msgs = (filteredMessages || data.messages);
              const avg = msgs.reduce((acc, m) => acc + (m.sentiment?.ensemble_score || 0), 0) / Math.max(1, msgs.length);
              if (avg >= 0.05) return 'Positive';
              if (avg <= -0.05) return 'Negative';
              return 'Neutral';
            })()}
            icon={overallSentimentEmoji[data.overall_sentiment.ensemble_label]} 
          />
        </div>
        <div className="col-lg-3 col-md-6">
          <StatCard 
            title="Primary Language" 
            value={(data.primary_language || '').toUpperCase()} 
            icon="🌍" 
          />
        </div>
        <div className="col-lg-3 col-md-6">
          <StatCard 
            title="Active Users" 
            value={userChartData.length} 
            icon="👥" 
          />
        </div>
      </div>

      {/* Filters and Export */}
      <div className="row g-4 mb-5">
        <div className="col-lg-6">
          <div className="card shadow-sm border-0 rounded-4 h-100" style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
            borderLeft: '4px solid #00bcd4'
          }}>
            <div className="card-body p-4">
              <h5 className="card-title mb-4" style={{ color: '#00695c', fontWeight: 700 }}>🔍 Filter Analysis</h5>
              <div className="row g-3">
                <div className="col-md-6">
                  <label htmlFor="startDate" className="form-label" style={{ color: '#00897b', fontWeight: 600 }}>Start Date</label>
                  <input 
                    type="date" 
                    className="form-control" 
                    id="startDate" 
                    value={startDate} 
                    onChange={(e) => setStartDate(e.target.value)}
                    style={{ borderColor: '#00bcd4', borderRadius: '8px' }}
                  />
                </div>
                <div className="col-md-6">
                  <label htmlFor="endDate" className="form-label" style={{ color: '#00897b', fontWeight: 600 }}>End Date</label>
                  <input 
                    type="date" 
                    className="form-control" 
                    id="endDate" 
                    value={endDate} 
                    onChange={(e) => setEndDate(e.target.value)}
                    style={{ borderColor: '#00bcd4', borderRadius: '8px' }}
                  />
                </div>
                <div className="col-12">
                  <label htmlFor="participant" className="form-label" style={{ color: '#00897b', fontWeight: 600 }}>Participant</label>
                  <select 
                    className="form-select" 
                    id="participant" 
                    value={selectedParticipant} 
                    onChange={(e) => setSelectedParticipant(e.target.value)}
                    style={{ borderColor: '#00bcd4', borderRadius: '8px' }}
                  >
                    <option value="">All Participants</option>
                    {participants.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div className="col-12 mt-3">
                  <button className="btn btn-primary w-100" style={{ borderRadius: '8px', fontWeight: 700 }} onClick={applyFilters}>
                    ✓ Apply Filters
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="card shadow-sm border-0 rounded-4 h-100" style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
            borderLeft: '4px solid #4db6ac'
          }}>
            <div className="card-body p-4">
              <h5 className="card-title mb-4" style={{ color: '#00695c', fontWeight: 700 }}>📊 Export Data</h5>
              <div className="d-grid gap-3">
                <button 
                  className="btn btn-primary" 
                  onClick={exportToCsv}
                  style={{ borderRadius: '8px', fontWeight: 700 }}
                >
                  📥 Export to CSV
                </button>
                <button 
                  className="btn btn-outline-secondary" 
                  onClick={exportToPdf}
                  style={{ borderColor: '#00897b', color: '#00897b', borderRadius: '8px', fontWeight: 700 }}
                >
                  📄 Export to PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts and Lists Row */}
      <div className="row g-4">
        <div className="col-lg-6">
          <UserChart data={userChartData} />
        </div>
        <div className="col-lg-3">
          <EmotionChart data={emotionChartData} />
        </div>
        <div className="col-lg-3">
          <LanguageDistributionChart data={languageChartData} />
        </div>
        <div className="col-lg-3">
          <EmojiList data={data.top_emojis} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
