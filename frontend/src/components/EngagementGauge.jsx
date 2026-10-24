import React from 'react';

const EngagementGauge = ({ prediction }) => {
  if (!prediction || !prediction.is_sufficient) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center' }}>
        <h3 style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '12px' }}>Student Engagement Level</h3>
        <div style={{
          padding: '16px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#fbbf24',
          fontSize: '0.85rem'
        }}>
          ⚠️ Not enough learning activity yet. Watch videos and attempt quizzes to generate real predictions.
        </div>
      </div>
    );
  }

  const level = prediction.engagement_level || 'Low';
  const confidence = Math.round((prediction.confidence || 0) * 100);

  const levelColors = {
    Low: { color: '#fb7185', bg: 'rgba(244, 63, 94, 0.15)', border: '#f43f5e' },
    Medium: { color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
    High: { color: '#34d399', bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981' }
  };

  const style = levelColors[level] || levelColors.Low;

  const lowPct = Math.round((prediction.low_probability || 0) * 100);
  const medPct = Math.round((prediction.medium_probability || 0) * 100);
  const highPct = Math.round((prediction.high_probability || 0) * 100);

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Predicted Engagement Level</h3>
        <span className={`badge badge-${level.toLowerCase()}`}>
          Bi-LSTM Model Active
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        {/* Large Central Gauge Badge */}
        <div style={{
          width: '120px',
          height: '120px',
          borderRadius: '50%',
          backgroundColor: style.bg,
          border: `3px solid ${style.border}`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 0 25px ${style.bg}`
        }}>
          <span style={{ fontSize: '1.4rem', fontWeight: 800, color: style.color }}>
            {level}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {confidence}% Conf.
          </span>
        </div>

        {/* Probability Distribution Bars */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <ProbBar label="Low Engagement" pct={lowPct} color="#f43f5e" />
          <ProbBar label="Medium Engagement" pct={medPct} color="#f59e0b" />
          <ProbBar label="High Engagement" pct={highPct} color="#10b981" />
        </div>
      </div>
    </div>
  );
};

const ProbBar = ({ label, pct, color }) => (
  <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px', color: 'var(--text-muted)' }}>
      <span>{label}</span>
      <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{pct}%</span>
    </div>
    <div style={{ height: '8px', backgroundColor: 'var(--bg-input)', borderRadius: '4px', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${pct}%`, backgroundColor: color, borderRadius: '4px', transition: 'width 0.5s ease' }} />
    </div>
  </div>
);

export default EngagementGauge;
