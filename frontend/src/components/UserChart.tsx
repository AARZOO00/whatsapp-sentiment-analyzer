import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface UserChartProps {
  data: { name: string; messages: number }[];
}

const UserChart: React.FC<UserChartProps> = ({ data }) => {
  return (
    <div className="card shadow-sm border-0 rounded-4 h-100" style={{
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
      borderLeft: '4px solid #00bcd4'
    }}>
      <div className="card-body p-4">
        <h5 className="card-title mb-4" style={{ color: '#00695c', fontWeight: 700 }}>👥 Most Active Users</h5>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#b3e5fc" />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#00897b' }} />
            <YAxis tick={{ fontSize: 12, fill: '#00897b' }} allowDecimals={false} />
            <Tooltip
              cursor={{ fill: 'rgba(0, 188, 212, 0.15)' }}
              contentStyle={{
                borderRadius: '12px',
                boxShadow: '0 8px 16px rgba(0, 150, 136, 0.2)',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.95)',
                color: '#00695c'
              }}
            />
            <Legend wrapperStyle={{ color: '#00897b', fontWeight: 600 }} />
            <Bar dataKey="messages" fill="#00bcd4" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default UserChart;