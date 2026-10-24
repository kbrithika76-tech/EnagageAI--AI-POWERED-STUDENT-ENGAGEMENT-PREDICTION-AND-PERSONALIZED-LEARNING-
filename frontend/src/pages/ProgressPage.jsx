import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { TrendingUp, Flame, Calendar, PlayCircle, HelpCircle, Clock } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar
} from 'recharts';

const ProgressPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/students/me/progress')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading progress analytics...
    </div>
  );

  const {
    weekly_activity = [], streak_days = 0, total_active_days = 0,
    total_events = 0, completed_videos = 0, total_content_available = 0,
    watch_time_minutes = 0, completed_quizzes = 0, avg_quiz_score = 0,
    topic_performance = []
  } = data || {};

  const videosPct = total_content_available > 0
    ? Math.round((completed_videos / total_content_available) * 100)
    : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <TrendingUp color="var(--accent-blue)" size={24} />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Progress Analytics</h1>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Your weekly learning activity, streaks, and topic-level performance.
        </p>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {[
          { icon: <Flame color="#f59e0b" size={22} />, label: 'Current Streak', value: `${streak_days} days` },
          { icon: <Calendar color="#3b82f6" size={22} />, label: 'Active Days', value: total_active_days },
          { icon: <PlayCircle color="#10b981" size={22} />, label: 'Videos Done', value: `${completed_videos} / ${total_content_available}` },
          { icon: <HelpCircle color="#8b5cf6" size={22} />, label: 'Quizzes Done', value: completed_quizzes },
          { icon: <Clock color="#06b6d4" size={22} />, label: 'Watch Time', value: `${watch_time_minutes} min` },
        ].map((c, i) => (
          <div key={i} className="glass-panel" style={{ padding: '18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'var(--bg-input)' }}>{c.icon}</div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.label}</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{c.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Weekly Activity Chart */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px' }}>Weekly Activity (Last 8 Weeks)</h3>
        <div style={{ width: '100%', height: '220px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weekly_activity}>
              <XAxis dataKey="week" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#131b2e', borderColor: 'rgba(255,255,255,0.1)' }} />
              <Bar dataKey="events" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Events" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Progress Bars + Topic Radar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Course Completion */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '20px' }}>Course Completion</h3>

          <ProgressBar label="Videos Completed" value={videosPct} color="var(--accent-emerald)" />
          <ProgressBar label="Avg Quiz Score" value={avg_quiz_score} color="var(--accent-blue)" />
          <ProgressBar
            label="Activity Consistency"
            value={Math.min(100, total_active_days * 5)}
            color="var(--accent-purple)"
          />
        </div>

        {/* Topic Radar */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px' }}>Topic Performance</h3>
          {topic_performance.length > 0 ? (
            <div style={{ width: '100%', height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={topic_performance}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="topic" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <Radar name="Avg Score" dataKey="avg_score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '20px 0' }}>
              Complete quizzes to see topic-level performance.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ProgressBar = ({ label, value, color }) => (
  <div style={{ marginBottom: '16px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontWeight: 700 }}>{Math.round(value)}%</span>
    </div>
    <div style={{ height: '8px', backgroundColor: 'var(--bg-input)', borderRadius: '4px', overflow: 'hidden' }}>
      <div style={{
        height: '100%', width: `${Math.min(100, value)}%`,
        backgroundColor: color, borderRadius: '4px',
        transition: 'width 0.6s ease'
      }} />
    </div>
  </div>
);

export default ProgressPage;
