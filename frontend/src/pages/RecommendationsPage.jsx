import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Sparkles, PlayCircle, HelpCircle, ArrowRight } from 'lucide-react';

const RecommendationsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/students/me/recommendations')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading recommendations...</div>;

  const { engagement_level, content_recommendations, quiz_recommendations } = data || {};

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Sparkles color="var(--accent-amber)" size={28} />
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.5px' }}>Recommended Learning</h1>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Tailored content and quizzes based on your current engagement level ({engagement_level || 'Low'}).
        </p>
      </div>

      {/* Recommended Videos */}
      <div>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PlayCircle color="#3b82f6" size={20} /> Recommended Video Lessons
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {content_recommendations?.map((item, idx) => (
            <div key={idx} className="glass-panel fade-in" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', animationDelay: `${idx * 0.1}s` }}>
              <div>
                <span className="badge badge-medium" style={{ marginBottom: '12px' }}>{item.difficulty}</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>{item.title}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>{item.reason}</p>
              </div>
              <button
                onClick={() => navigate(`/videos/${item.content_id}`)}
                className="btn-primary"
                style={{ padding: '8px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                Watch Video <ArrowRight size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Quizzes */}
      <div style={{ marginTop: '16px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <HelpCircle color="#f59e0b" size={20} /> Recommended Quizzes
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {quiz_recommendations?.map((quiz, idx) => (
            <div key={idx} className="glass-panel fade-in" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', animationDelay: `${idx * 0.1 + 0.2}s` }}>
              <div>
                <span className="badge badge-high" style={{ marginBottom: '12px' }}>{quiz.difficulty}</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>{quiz.title}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>{quiz.reason}</p>
              </div>
              <button
                onClick={() => navigate(`/quizzes/${quiz.quiz_id}`)}
                className="btn-secondary"
                style={{ padding: '8px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                Attempt Quiz <ArrowRight size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecommendationsPage;
