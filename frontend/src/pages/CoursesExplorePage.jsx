import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Search, Filter, PlayCircle, Clock, ArrowRight } from 'lucide-react';

const CoursesExplorePage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/content/videos')
      .then(res => setVideos(res.data || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = videos.filter(v => {
    const matchSearch = v.title.toLowerCase().includes(search.toLowerCase()) ||
      (v.module || '').toLowerCase().includes(search.toLowerCase());
    const matchDiff = filterDifficulty === 'all' || v.difficulty === filterDifficulty;
    return matchSearch && matchDiff;
  });

  // Group by module
  const grouped = filtered.reduce((acc, v) => {
    const mod = v.module || 'General';
    if (!acc[mod]) acc[mod] = [];
    acc[mod].push(v);
    return acc;
  }, {});

  const diffBadge = (d) => {
    const map = { beginner: 'badge-high', intermediate: 'badge-medium', advanced: 'badge-low' };
    return map[d] || 'badge-medium';
  };

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading course catalog...
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Explore Courses</h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Browse the full catalog of video lessons across all topics and difficulty levels.
        </p>
      </div>

      {/* Search + Filter Bar */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
          <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search topics or lesson names..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%', padding: '10px 12px 10px 38px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border-color)',
              color: 'white', outline: 'none', fontSize: '0.88rem'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Filter size={15} color="var(--text-muted)" />
          {['all', 'beginner', 'intermediate', 'advanced'].map(d => (
            <button
              key={d}
              onClick={() => setFilterDifficulty(d)}
              style={{
                padding: '6px 14px', borderRadius: '999px', fontSize: '0.78rem', fontWeight: 600,
                border: filterDifficulty === d ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                backgroundColor: filterDifficulty === d ? 'rgba(59,130,246,0.15)' : 'var(--bg-input)',
                color: filterDifficulty === d ? 'var(--accent-blue)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
        Showing {filtered.length} lesson{filtered.length !== 1 ? 's' : ''}
      </div>

      {/* Grouped by module */}
      {Object.entries(grouped).map(([module, items]) => (
        <div key={module}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '0.8rem' }}>
            📁 {module}
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {items.map(v => (
              <div key={v.id} className="glass-panel" style={{
                padding: '20px', cursor: 'pointer',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease'
              }}
                onClick={() => navigate(`/videos/${v.id}`)}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = 'translateY(-3px)';
                  e.currentTarget.style.boxShadow = '0 12px 32px rgba(0,0,0,0.4)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span className={`badge ${diffBadge(v.difficulty)}`}>{v.difficulty}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    {v.duration_seconds ? `${Math.round(v.duration_seconds / 60)} min` : '—'}
                  </span>
                </div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '8px', lineHeight: 1.4 }}>{v.title}</h3>
                {v.description && (
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '14px', lineHeight: 1.5 }}>
                    {v.description.slice(0, 90)}{v.description.length > 90 ? '…' : ''}
                  </p>
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-blue)', fontSize: '0.82rem', fontWeight: 600 }}>
                  <PlayCircle size={14} /> Watch Lesson <ArrowRight size={13} />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No lessons match your search. Try different keywords or remove the difficulty filter.
        </div>
      )}
    </div>
  );
};

export default CoursesExplorePage;
