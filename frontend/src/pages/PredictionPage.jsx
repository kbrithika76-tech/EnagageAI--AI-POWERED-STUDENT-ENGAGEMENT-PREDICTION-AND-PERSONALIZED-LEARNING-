import React, { useState, useEffect } from 'react';
import api from '../services/api';
import EngagementGauge from '../components/EngagementGauge';
import { RefreshCw, BrainCircuit, Sparkles, AlertCircle } from 'lucide-react';

const PredictionPage = () => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPrediction = async () => {
    try {
      const res = await api.get('/students/me/prediction');
      setPrediction(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const res = await api.post('/students/me/prediction/refresh');
      setPrediction(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading prediction metrics...</div>;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Student Engagement Level</h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Real-time student engagement analysis and forecasting.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
          {refreshing ? 'Updating Data...' : 'Refresh Engagement Level'}
        </button>
      </div>

      <EngagementGauge prediction={prediction} />

      {/* System Performance Details Card */}
      <div className="glass-panel fade-in" style={{ padding: '28px', animationDelay: '0.2s' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="var(--accent-purple)" /> System Information
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '0.85rem' }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Engine:</span>
            <div style={{ fontWeight: 700 }}>Learning Analytics System</div>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Data Points:</span>
            <div style={{ fontWeight: 700 }}>Activity timeline tracked</div>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Profile Features:</span>
            <div style={{ fontWeight: 700 }}>Included</div>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Test Set Accuracy:</span>
            <div style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>99.37% (Macro F1 = 0.9937)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionPage;
