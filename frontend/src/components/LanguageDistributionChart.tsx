import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface LanguageDistributionChartProps {
  data: { name: string; value: number }[];
}

// Water & Shine theme colors
const COLORS = ['#00bcd4', '#0097a7', '#4db6ac', '#80cbc4', '#26a69a', '#00897b'];

const LanguageDistributionChart: React.FC<LanguageDistributionChartProps> = ({ data }) => {
  return (
    <div className="card shadow-sm border-0 rounded-4 h-100" style={{
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
      borderLeft: '4px solid #0097a7'
    }}>
      <div className="card-body d-flex flex-column p-4">
        <h5 className="card-title mb-4" style={{ color: '#00695c', fontWeight: 700 }}>🌍 Language Distribution</h5>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={75}
              fill="#00bcd4"
              paddingAngle={3}
              dataKey="value"
              nameKey="name"
              label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
            >
              {data.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number | undefined) => (value !== undefined ? `${value.toFixed(1)}%` : '')}
              contentStyle={{
                borderRadius: '12px',
                boxShadow: '0 8px 16px rgba(0, 150, 136, 0.2)',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.95)',
                color: '#00695c'
              }}
            />
            <Legend iconSize={10} wrapperStyle={{ color: '#00897b', fontWeight: 600 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default LanguageDistributionChart;