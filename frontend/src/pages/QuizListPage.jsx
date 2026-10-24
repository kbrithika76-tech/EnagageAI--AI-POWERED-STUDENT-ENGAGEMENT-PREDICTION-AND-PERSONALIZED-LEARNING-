import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { HelpCircle, CheckCircle, Award, ArrowRight } from 'lucide-react';

const QuizListPage = () => {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/quizzes')
      .then(res => setQuizzes(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading quizzes...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Interactive Quizzes</h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Evaluate your understanding to boost your student engagement score.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
        {quizzes.map(q => {
          const att = q.user_attempt || {};

          return (
            <div
              key={q.id}
              className="glass-panel"
              style={{
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '16px'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span className="badge badge-medium">{q.difficulty}</span>
                  {att.attempted && (
                    <span className="badge badge-high">
                      <CheckCircle size={12} /> {Math.round(att.best_score_pct)}% Score
                    </span>
                  )}
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '6px' }}>{q.title}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{q.description}</p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{q.question_count} Questions</span>
                <button
                  onClick={() => navigate(`/quizzes/${q.id}`)}
                  className="btn-primary"
                  style={{ padding: '6px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {att.attempted ? 'Retake Quiz' : 'Start Quiz'}
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default QuizListPage;
