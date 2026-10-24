import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { CheckCircle, XCircle, ArrowLeft, RotateCcw, Target } from 'lucide-react';

const QuizResultPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/quizzes/${id}/attempt/latest`)
      .then(res => setResult(res.data))
      .catch(err => {
        console.error(err);
        // Fallback if no attempt found
        if (err.response?.status === 404) {
          navigate(`/quizzes/${id}`);
        }
      })
      .finally(() => setLoading(false));
  }, [id, navigate]);

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading quiz results...
    </div>
  );

  if (!result) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header & Score Card */}
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', borderTop: result.passed ? '4px solid #10b981' : '4px solid #f43f5e' }}>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '8px' }}>{result.quiz_title} — Results</h1>
        <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Completed on {new Date(result.completed_at).toLocaleString()}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '40px' }}>
          <div>
            <div style={{ fontSize: '3rem', fontWeight: 900, color: result.passed ? '#10b981' : '#f43f5e', lineHeight: 1 }}>
              {result.score_pct}%
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px', fontWeight: 600, textTransform: 'uppercase' }}>
              {result.passed ? 'Passed' : 'Needs Review'}
            </div>
          </div>
          <div style={{ textAlign: 'left', borderLeft: '1px solid var(--border-color)', paddingLeft: '40px' }}>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Score</span>
              <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{result.score} / {result.total_marks}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Accuracy</span>
              <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                {result.questions_detail.filter(q => q.is_correct).length} / {result.questions_detail.length} correct
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '32px' }}>
          <button onClick={() => navigate('/quizzes')} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ArrowLeft size={16} /> Back to Quizzes
          </button>
          <button onClick={() => navigate(`/quizzes/${id}`)} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RotateCcw size={16} /> Retake Quiz
          </button>
        </div>
      </div>

      {/* Questions Review */}
      <div>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={20} color="var(--accent-blue)" /> Detailed Review
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {result.questions_detail.map((q, idx) => (
            <div key={q.id} className="glass-panel" style={{
              padding: '24px',
              borderLeft: q.is_correct ? '4px solid #10b981' : '4px solid #f43f5e'
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                {q.is_correct ? <CheckCircle color="#10b981" size={20} style={{ flexShrink: 0, marginTop: '2px' }} /> : <XCircle color="#f43f5e" size={20} style={{ flexShrink: 0, marginTop: '2px' }} />}
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px', lineHeight: 1.5 }}>
                    <span style={{ color: 'var(--text-muted)', marginRight: '8px' }}>{idx + 1}.</span>
                    {q.question}
                  </h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {['a', 'b', 'c', 'd'].map(optKey => {
                      const optText = q.options[optKey];
                      if (!optText) return null;

                      const isSelected = q.user_answer?.toLowerCase() === optKey;
                      const isCorrect = q.correct_option?.toLowerCase() === optKey;

                      let bg = 'var(--bg-input)';
                      let border = '1px solid var(--border-color)';
                      let text = 'var(--text-main)';

                      if (isCorrect) {
                        bg = 'rgba(16,185,129,0.15)';
                        border = '1px solid #10b981';
                        text = '#34d399';
                      } else if (isSelected && !isCorrect) {
                        bg = 'rgba(244,63,94,0.15)';
                        border = '1px solid #f43f5e';
                        text = '#fb7185';
                      }

                      return (
                        <div key={optKey} style={{
                          padding: '12px 16px', borderRadius: 'var(--radius-sm)',
                          backgroundColor: bg, border, color: text,
                          display: 'flex', justifyContent: 'space-between',
                          fontSize: '0.9rem'
                        }}>
                          <span>{optText}</span>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                            {isCorrect && isSelected && '✓ Correct'}
                            {isCorrect && !isSelected && '✓ Correct Answer'}
                            {isSelected && !isCorrect && '✗ Your Answer'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuizResultPage;
