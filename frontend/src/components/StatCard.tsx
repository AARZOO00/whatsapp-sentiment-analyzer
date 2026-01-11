import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, className = '' }) => {
  return (
    <div 
      className={`card kpi-card shadow-sm border-0 rounded-4 h-100 ${className}`}
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
        borderLeft: '4px solid #00bcd4',
        transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        position: 'relative',
        overflow: 'hidden'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-10px) scale(1.05)';
        e.currentTarget.style.boxShadow = '0 20px 40px rgba(0, 150, 136, 0.25)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0) scale(1)';
        e.currentTarget.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
      }}
    >
      <div className="card-body" style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="icon" style={{ 
          fontSize: '3rem', 
          marginBottom: '0.8rem',
          display: 'inline-block',
          animation: 'float 3s ease-in-out infinite'
        }}>
          {icon}
        </div>
        <h5 className="card-title text-uppercase" style={{ 
          color: '#00695c',
          fontSize: '0.9rem',
          letterSpacing: '1.5px',
          fontWeight: 700,
          marginBottom: '0.5rem'
        }}>
          {title}
        </h5>
        <p className="card-text" style={{
          fontSize: '2rem',
          fontWeight: 800,
          background: 'linear-gradient(135deg, #00695c 0%, #00897b 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          margin: 0
        }}>
          {value}
        </p>
      </div>
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
};

export default StatCard;