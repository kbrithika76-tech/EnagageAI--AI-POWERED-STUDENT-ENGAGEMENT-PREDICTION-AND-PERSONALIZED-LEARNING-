import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { BookOpen, PlayCircle, CheckCircle, Clock, ArrowRight, Sparkles } from 'lucide-react';

const MyLearningPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/students/me/my-learning')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading your learning activity...
    </div>
  );

  const { in_progress = [], completed = [], suggested = [] } = data || {};

  const ContentCard = ({ item, done }) => {
    const duration = item.duration_seconds ? `${Math.round(item.duration_seconds / 60)} min` : '—';
    return (
      <div className="glass-panel" style={{
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        border: done ? '1px solid rgba(16,185,129,0.25)' : '1px solid var(--border-color)',
        transition: 'transform 0.2s ease'
      }}
        onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
      >
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span className={`badge badge-${item.difficulty === 'advanced' ? 'low' : item.difficulty === 'intermediate' ? 'medium' : 'high'}`}>
              {item.difficulty}
            </span>
            {done && <CheckCircle size={18} color="#10b981" />}
          </div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '6px', lineHeight: 1.4 }}>{item.title}</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
            {item.module} &nbsp;·&nbsp; <Clock size={11} style={{ verticalAlign: 'middle' }} /> {duration}
          </p>

          {!done && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.73rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                <span>Progress</span>
                <span>{item.watch_pct || 0}%</span>
              </div>
              <div style={{ height: '6px', backgroundColor: 'var(--bg-input)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${item.watch_pct || 0}%`, backgroundColor: 'var(--accent-blue)', borderRadius: '3px' }} />
              </div>
            </div>
          )}
        </div>

        <button
          onClick={() => navigate(`/videos/${item.id}`)}
          className={done ? 'btn-secondary' : 'btn-primary'}
          style={{ width: '100%', padding: '8px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
        >
          <PlayCircle size={14} /> {done ? 'Rewatch' : item.watch_pct > 0 ? 'Continue' : 'Start'} <ArrowRight size={13} />
        </button>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <BookOpen color="var(--accent-blue)" size={24} />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>My Learning</h1>
      </div>

      {/* In Progress */}
      {in_progress.length > 0 && (
        <section>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', color: '#60a5fa' }}>
            ▶ In Progress ({in_progress.length})
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {in_progress.map(item => <ContentCard key={item.id} item={item} done={false} />)}
          </div>
        </section>
      )}

      {/* Completed */}
      {completed.length > 0 && (
        <section>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', color: '#34d399' }}>
            ✓ Completed ({completed.length})
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {completed.map(item => <ContentCard key={item.id} item={item} done={true} />)}
          </div>
        </section>
      )}

      {/* Suggested Starts (cold start) */}
      {suggested.length > 0 && (
        <section>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles color="#f59e0b" size={18} />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Suggested to Start</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {suggested.map(item => <ContentCard key={item.id} item={{ ...item, watch_pct: 0 }} done={false} />)}
          </div>
        </section>
      )}

      {in_progress.length === 0 && completed.length === 0 && suggested.length === 0 && (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📚</div>
          <p style={{ color: 'var(--text-muted)' }}>No learning activity yet. Start watching a video to begin!</p>
          <button onClick={() => navigate('/videos')} className="btn-primary" style={{ marginTop: '16px', padding: '10px 24px' }}>
            Browse Videos
          </button>
        </div>
      )}
    </div>
  );
};

export default MyLearningPage;
