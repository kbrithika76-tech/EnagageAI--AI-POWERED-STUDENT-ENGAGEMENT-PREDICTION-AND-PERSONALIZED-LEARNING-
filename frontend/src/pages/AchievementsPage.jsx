import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Award, Flame, Zap, Star } from 'lucide-react';

const AchievementsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/students/me/achievements')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading achievements...
    </div>
  );

  const {
    xp = 0, level = 1, xp_to_next_level = 200,
    streak_days = 0, badges = [], completed_videos = 0, completed_quizzes = 0
  } = data || {};

  const xpPct = Math.min(100, Math.round((xp % 200) / 200 * 100));
  const earnedBadges = badges.filter(b => b.earned);
  const lockedBadges = badges.filter(b => !b.earned);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Award color="#f59e0b" size={26} />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Achievements & Gamification</h1>
      </div>

      {/* XP & Level Banner */}
      <div className="glass-panel" style={{
        padding: '28px',
        background: 'linear-gradient(135deg, rgba(59,130,246,0.12) 0%, rgba(139,92,246,0.12) 100%)',
        border: '1px solid rgba(139,92,246,0.25)',
        display: 'grid',
        gridTemplateColumns: 'auto 1fr auto',
        gap: '24px',
        alignItems: 'center'
      }}>
        {/* Level Badge */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '72px', height: '72px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.5rem', fontWeight: 900, boxShadow: '0 0 24px rgba(245,158,11,0.35)'
          }}>
            {level}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '6px' }}>LEVEL</div>
        </div>

        {/* XP Bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 700 }}>
              <Zap size={14} style={{ verticalAlign: 'middle', marginRight: '4px', color: '#f59e0b' }} />
              {xp} XP Total
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{xp_to_next_level} XP to Level {level + 1}</span>
          </div>
          <div style={{ height: '12px', backgroundColor: 'var(--bg-input)', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{
              height: '100%', width: `${xpPct}%`,
              background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
              borderRadius: '6px', transition: 'width 0.8s ease'
            }} />
          </div>
          <div style={{ display: 'flex', gap: '20px', marginTop: '12px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <span>🎬 {completed_videos} videos</span>
            <span>📝 {completed_quizzes} quizzes</span>
            <span>🔥 {streak_days}-day streak</span>
          </div>
        </div>

        {/* Streak */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem' }}>🔥</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#f59e0b' }}>{streak_days}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DAY STREAK</div>
        </div>
      </div>

      {/* Earned Badges */}
      <div>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Star color="#f59e0b" size={18} /> Earned Badges ({earnedBadges.length})
        </h2>
        {earnedBadges.length === 0 ? (
          <div className="glass-panel" style={{ padding: '28px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No badges earned yet — start watching videos and taking quizzes! 🚀
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
            {earnedBadges.map(badge => (
              <div key={badge.id} className="glass-panel" style={{
                padding: '20px', textAlign: 'center',
                border: '1px solid rgba(245,158,11,0.3)',
                background: 'rgba(245,158,11,0.06)',
                transition: 'transform 0.2s ease'
              }}
                onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
              >
                <div style={{ fontSize: '2.4rem', marginBottom: '8px' }}>{badge.icon}</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fbbf24', marginBottom: '4px' }}>{badge.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{badge.description}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Locked Badges */}
      {lockedBadges.length > 0 && (
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', color: 'var(--text-muted)' }}>
            🔒 Locked Badges — Keep going!
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
            {lockedBadges.map(badge => (
              <div key={badge.id} style={{
                padding: '20px', textAlign: 'center',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                opacity: 0.5
              }}>
                <div style={{ fontSize: '2.4rem', marginBottom: '8px', filter: 'grayscale(1)' }}>{badge.icon}</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '4px' }}>{badge.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{badge.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AchievementsPage;
