import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { AlertTriangle, CheckCircle, ShieldAlert, Info } from 'lucide-react';

const EarlyWarningPage = () => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/students/me/prediction')
      .then(res => setPrediction(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading risk status...</div>;

  const isInsufficient = !prediction || !prediction.is_sufficient;
  const level = prediction?.engagement_level || 'Low';
  const lowProb = Math.round((prediction?.low_probability || 0) * 100);

  let riskStatus = 'LOW RISK';
  let riskColor = '#10b981';
  let riskBg = 'rgba(16, 185, 129, 0.15)';

  if (level === 'Low' || lowProb >= 50) {
    riskStatus = 'HIGH RISK';
    riskColor = '#f43f5e';
    riskBg = 'rgba(244, 63, 94, 0.15)';
  } else if (level === 'Medium' || lowProb >= 30) {
    riskStatus = 'MEDIUM RISK';
    riskColor = '#f59e0b';
    riskBg = 'rgba(245, 158, 11, 0.15)';
  }

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.5px' }}>Early Support System</h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Real-time support assessment based on your activity trends.
        </p>
      </div>

      {/* Main Risk Status Card */}
      <div className="glass-panel fade-in" style={{ padding: '36px', textAlign: 'center', backgroundColor: riskBg, animationDelay: '0.1s' }}>
        <ShieldAlert size={56} color={riskColor} style={{ marginBottom: '16px' }} />
        <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
          Current Academic Risk Status
        </div>
        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, color: riskColor, margin: '12px 0', letterSpacing: '-1px' }}>
          {isInsufficient ? 'PENDING ACTIVITY' : riskStatus}
        </h2>
        <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto 20px auto', lineHeight: 1.6 }}>
          {isInsufficient
            ? 'Complete your onboarding videos and quizzes to compute your personalized risk profile.'
            : `Your low-engagement probability is currently assessed at ${lowProb}%.`}
        </p>
      </div>

      {/* Warning Indicators List */}
      <div className="glass-panel fade-in" style={{ padding: '28px', animationDelay: '0.2s' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px' }}>Detected Risk Factors & Indicators</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <RiskFactor
            active={level === 'Low'}
            title="Low Engagement Level Detected"
            desc="System analysis indicates potential for decreased activity."
          />
          <RiskFactor
            active={lowProb >= 40}
            title="Elevated Need for Support"
            desc={`System assigned ${lowProb}% probability of needing support.`}
          />
          <RiskFactor
            active={false}
            title="Quiz Completion Rate Warning"
            desc="Sustained quiz participation maintains active engagement status."
          />
        </div>
      </div>
    </div>
  );
};

const RiskFactor = ({ active, title, desc }) => (
  <div style={{
    padding: '14px 18px',
    borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--bg-input)',
    border: `1px solid ${active ? 'rgba(244, 63, 94, 0.4)' : 'var(--border-color)'}`,
    display: 'flex',
    alignItems: 'center',
    gap: '14px'
  }}>
    {active ? <AlertTriangle color="#f43f5e" size={20} /> : <CheckCircle color="#10b981" size={20} />}
    <div>
      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: active ? '#fb7185' : 'var(--text-main)' }}>{title}</div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{desc}</div>
    </div>
  </div>
);

export default EarlyWarningPage;
