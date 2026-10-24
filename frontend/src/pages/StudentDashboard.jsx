import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { BrainCircuit, PlayCircle, Award, TrendingUp, BarChart2, AlertTriangle, ArrowRight } from 'lucide-react';

const StudentDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = () => {
    api.get('/students/me/dashboard')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  const handleRefreshPrediction = () => {
    setRefreshing(true);
    api.post('/students/me/prediction/refresh')
      .then(() => fetchDashboard())
      .catch(err => console.error(err))
      .finally(() => setRefreshing(false));
  };

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading your dashboard...
    </div>
  );

  const { student, stats, prediction } = data || {};
  const levelColor = prediction?.engagement_level === 'High' ? '#10b981' : prediction?.engagement_level === 'Medium' ? '#f59e0b' : '#f43f5e';

  // Dummy trend data if not provided by backend yet
  const trendData = data?.activity_chart || [
    { week: 'W1', activity: 12 }, { week: 'W2', activity: 18 },
    { week: 'W3', activity: 15 }, { week: 'W4', activity: 25 },
    { week: 'W5', activity: 20 }, { week: 'W6', activity: 30 },
    { week: 'W7', activity: (stats?.total_events || 20) + 10 }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-0.5px' }}>Welcome back, {student?.name?.split(' ')[0]} 👋</h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Ready to continue your learning journey?
          </p>
        </div>
        <button
          onClick={handleRefreshPrediction}
          disabled={refreshing}
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          {refreshing ? <div className="spinner" style={{ width: '14px', height: '14px' }} /> : <BrainCircuit size={16} />}
          {refreshing ? 'Updating Profile...' : 'Refresh Activity Status'}
        </button>
      </div>

      {/* Quick Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {[
          { icon: <TrendingUp size={20} color="#10b981" />, label: 'Engagement Level', value: prediction?.engagement_level || 'N/A' },
          { icon: <BarChart2 size={20} color="#3b82f6" />, label: 'Avg Quiz Score', value: `${stats?.avg_quiz_score || 0}%` },
          { icon: <PlayCircle size={20} color="#8b5cf6" />, label: 'Videos Watched', value: stats?.completed_videos || 0 },
          { icon: <Award size={20} color="#f59e0b" />, label: 'Quizzes Passed', value: stats?.completed_quizzes || 0 },
        ].map((s, i) => (
          <div key={i} className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'var(--bg-input)' }}>
              {s.icon}
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>{s.label}</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{s.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Continue Learning Banner */}
      <div className="glass-panel fade-in" style={{ 
        padding: '28px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
        border: '1px solid rgba(59, 130, 246, 0.2)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
           <div style={{ width: '64px', height: '64px', borderRadius: '16px', backgroundColor: 'var(--bg-input)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
             <PlayCircle size={32} color="var(--accent-blue)" />
           </div>
           <div>
             <div style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>Up Next</div>
             <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: '0 0 4px 0' }}>Introduction to Deep Learning</h2>
             <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Module 1 • Deep Learning Course</div>
           </div>
        </div>
        <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => navigate('/courses')}>
          Continue Learning <ArrowRight size={18} />
        </button>
      </div>

      {/* Main Grid: Activity Trend + Prediction Card */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '24px' }}>
        {/* Activity Chart */}
        <div className="glass-panel fade-in" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px' }}>Weekly Learning Activity</h3>
          <div style={{ height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorAct" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="week" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#131b2e', borderColor: 'rgba(255,255,255,0.1)' }} />
                <Area type="monotone" dataKey="activity" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorAct)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Prediction Card */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <BrainCircuit size={24} color="var(--accent-blue)" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Engagement Level</h3>
          </div>
          
          <div style={{ textAlign: 'center', margin: '20px 0' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Current Status</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: levelColor }}>
              {prediction?.engagement_level || 'Pending'}
            </div>
          </div>

          {prediction?.engagement_level === 'Low' && (
            <div style={{ marginTop: 'auto', padding: '12px', backgroundColor: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.3)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f43f5e', fontWeight: 600, marginBottom: '4px', fontSize: '0.85rem' }}>
                <AlertTriangle size={16} /> Early Support
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Your recent learning activity is lower than usual. Try completing one recommended lesson today!
              </div>
            </div>
          )}

          <button className="btn-secondary" style={{ marginTop: '20px', width: '100%' }} onClick={() => navigate('/explanation')}>
            View Learning Insights
          </button>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
