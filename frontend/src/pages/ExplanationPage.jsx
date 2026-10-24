import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, Cell } from 'recharts';
import { BrainCircuit, Clock, BarChart2 } from 'lucide-react';

const ExplanationPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/students/me/explanation')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading Learning Insights...
    </div>
  );

  const { attention_weights = [], shap_values = {} } = data || {};

  // Sort and format attention chart data
  const sortedAttn = [...attention_weights].sort((a, b) => a.week - b.week);
  const attnChartData = sortedAttn.map(w => ({ week: `W${w.week}`, weight: w.weight }));
  
  // Sort and format SHAP chart data
  const shapData = Object.entries(shap_values)
    .map(([feature, value]) => ({ feature, value }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10); // top 10 factors

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <BrainCircuit size={28} color="var(--accent-purple)" />
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.5px' }}>How Can I Improve?</h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Understand the key factors and learning weeks driving your engagement level.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* SHAP Chart (Key Learning Factors) */}
        <div className="glass-panel fade-in" style={{ padding: '28px', animationDelay: '0.1s' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <BarChart2 size={20} color="var(--accent-blue)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Key Learning Factors</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '24px' }}>
            These learning activities contributed most to your current engagement level.
          </p>

          {shapData.length > 0 ? (
            <div style={{ width: '100%', height: '280px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={shapData} layout="vertical" margin={{ left: 80, right: 20 }}>
                  <XAxis type="number" stroke="#6b7280" fontSize={10} hide />
                  <YAxis dataKey="feature" type="category" stroke="#6b7280" fontSize={11} width={80} tickFormatter={(val) => val.length > 15 ? val.substring(0, 15) + '...' : val} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#131b2e', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {shapData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#10b981' : '#f43f5e'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '20px 0', fontStyle: 'italic' }}>No factor data available yet.</div>
          )}
        </div>

        {/* Attention Chart (Important Learning Weeks) */}
        <div className="glass-panel fade-in" style={{ padding: '28px', animationDelay: '0.2s' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Clock size={20} color="var(--accent-purple)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Important Learning Weeks</h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            These weeks had stronger influence on your engagement pattern.
          </p>

          <div style={{ width: '100%', height: '260px' }}>
            {attnChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={attnChartData}>
                  <XAxis dataKey="week" stroke="#6b7280" fontSize={9} interval={3} />
                  <YAxis stroke="#6b7280" fontSize={10} hide />
                  <Tooltip contentStyle={{ backgroundColor: '#131b2e', borderColor: 'rgba(255,255,255,0.1)' }} />
                  <Line type="monotone" dataKey="weight" stroke="#8b5cf6" strokeWidth={3} dot={{ fill: '#8b5cf6', r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '20px 0' }}>No timeline data available yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExplanationPage;
