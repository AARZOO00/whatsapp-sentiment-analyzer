import React from 'react';

interface EmojiListProps {
  data: [string, number][];
}

const EmojiList: React.FC<EmojiListProps> = ({ data }) => {
  return (
    <div className="card shadow-sm border-0 rounded-4 h-100" style={{
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
      borderLeft: '4px solid #26a69a'
    }}>
      <div className="card-body p-4">
        <h5 className="card-title mb-4" style={{ color: '#00695c', fontWeight: 700 }}>😊 Top Emojis</h5>
        {data.length > 0 ? (
          <div className="list-group list-group-flush">
            {data.map(([emoji, count], index) => (
              <div 
                key={emoji} 
                className="list-group-item border-0 px-0 py-3"
                style={{
                  background: index % 2 === 0 ? 'rgba(0, 188, 212, 0.05)' : 'transparent',
                  borderRadius: '8px',
                  marginBottom: '0.25rem',
                  transition: 'all 0.3s ease'
                }}
              >
                <div className="d-flex justify-content-between align-items-center">
                  <span style={{ fontSize: '1.85rem' }}>{emoji}</span>
                  <span 
                    className="badge rounded-pill fs-6"
                    style={{
                      background: 'linear-gradient(135deg, #00897b 0%, #00bcd4 100%)',
                      color: 'white',
                      fontWeight: 700,
                      padding: '0.4rem 0.8rem'
                    }}
                  >
                    {count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-muted mt-4" style={{ color: '#00897b' }}>
            <p style={{ fontSize: '0.95rem' }}>No emojis found in this chat.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmojiList;