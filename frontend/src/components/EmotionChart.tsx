import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface EmotionChartProps {
  data: { name: string; value: number }[];
}

const COLORS: { [key: string]: string } = {
  'Joy': '#00bcd4',
  'Anger': '#ff7043',
  'Sadness': '#5c6bc0',
  'Fear': '#9575cd',
  'Surprise': '#ffb74d',
  'Neutral': '#80cbc4',
  'Love': '#ef5350',
  'Positive': '#26a69a',
  'Negative': '#dc3545',
};
const FALLBACK_COLOR = '#00bcd4';

const EmotionChart: React.FC<EmotionChartProps> = ({ data }) => {
  return (
    <div className="card shadow-sm border-0 rounded-4 h-100" style={{
      background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(224,247,255,0.8) 100%)',
      borderLeft: '4px solid #00bcd4'
    }}>
      <div className="card-body d-flex flex-column p-4">
        <h5 className="card-title mb-4" style={{ color: '#00695c', fontWeight: 700 }}>😊 Emotion Distribution</h5>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              innerRadius={50}
              outerRadius={75}
              fill="#00bcd4"
              paddingAngle={3}
              dataKey="value"
              nameKey="name"
              label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
            >
              {data.map((entry) => (
                <Cell key={`cell-${entry.name}`} fill={COLORS[entry.name] || FALLBACK_COLOR} />
              ))}
            </Pie>
            <Tooltip 
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

export default EmotionChart;
