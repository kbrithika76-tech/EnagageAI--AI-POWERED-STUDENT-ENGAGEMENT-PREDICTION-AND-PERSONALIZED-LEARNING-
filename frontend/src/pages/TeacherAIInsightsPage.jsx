import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { BrainCircuit, Zap, TrendingUp, AlertTriangle, Users, BarChart2 } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = { High: '#10b981', Medium: '#f59e0b', Low: '#f43f5e', 'Insufficient Activity': '#6b7280' };

const TeacherAIInsightsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/teacher/ai-insights')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading class insights...
    </div>
  );

  const {
    total_students = 0,
    engagement_distribution = {},
    inactive_this_week = 0,
    students_with_no_quiz = 0,
    avg_class_quiz_score = 0,
    insights = []
  } = data || {};

  const pieData = Object.entries(engagement_distribution)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  const insightBg = {
    positive: 'rgba(16,185,129,0.08)',
    warning: 'rgba(245,158,11,0.08)',
    alert:   'rgba(244,63,94,0.08)',
    info:    'rgba(59,130,246,0.08)',
  };
  const insightBorder = {
    positive: 'rgba(16,185,129,0.25)',
    warning:  'rgba(245,158,11,0.25)',
    alert:    'rgba(244,63,94,0.25)',
    info:     'rgba(59,130,246,0.25)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <BrainCircuit size={26} color="var(--accent-purple)" />
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Learning Insights</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Engagement predictions and activity analysis for your class.
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {[
          { icon: <Users size={20} color="#3b82f6" />, label: 'Total Students', value: total_students },
          { icon: <TrendingUp size={20} color="#10b981" />, label: 'High Engagement', value: engagement_distribution.High || 0 },
          { icon: <AlertTriangle size={20} color="#f43f5e" />, label: 'Low Engagement', value: engagement_distribution.Low || 0 },
          { icon: <Zap size={20} color="#f59e0b" />, label: 'Inactive This Week', value: inactive_this_week },
          { icon: <BarChart2 size={20} color="#8b5cf6" />, label: 'Avg Quiz Score', value: `${avg_class_quiz_score}%` },
        ].map((s, i) => (
          <div key={i} className="glass-panel" style={{ padding: '18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'var(--bg-input)' }}>{s.icon}</div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{s.label}</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800 }}>{s.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Engagement Distribution Chart + Insight Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: '24px' }}>
        {/* Pie Chart */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px' }}>Engagement Distribution</h3>
          {pieData.length > 0 ? (
            <div style={{ height: '240px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} paddingAngle={3}>
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={COLORS[entry.name] || '#6b7280'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#131b2e', borderColor: 'rgba(255,255,255,0.1)' }} />
                  <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '20px 0' }}>
              No prediction data available yet.
            </div>
          )}
        </div>

        {/* Insight Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Recommendations for You</h3>
          {insights.length === 0 ? (
            <div className="glass-panel" style={{ padding: '24px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              All students are on track! No interventions needed right now. ✅
            </div>
          ) : (
            insights.map((ins, i) => (
              <div key={i} style={{
                padding: '16px 20px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: insightBg[ins.type] || 'var(--bg-card)',
                border: `1px solid ${insightBorder[ins.type] || 'var(--border-color)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>{ins.icon}</span>
                  <div>
                    <p style={{ fontSize: '0.88rem', fontWeight: 600, marginBottom: '4px' }}>
                      {ins.message.replace('predicted by the Bi-LSTM model', 'based on recent learning activity')}
                    </p>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      💡 <em>{ins.action}</em>
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default TeacherAIInsightsPage;
