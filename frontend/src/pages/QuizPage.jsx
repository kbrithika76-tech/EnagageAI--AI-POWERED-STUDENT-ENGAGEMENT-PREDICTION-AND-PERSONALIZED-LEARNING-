import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { ChevronRight, ChevronLeft, CheckCircle, Clock } from 'lucide-react';

const QuizPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  
  // Timer tracking
  const [startTime, setStartTime] = useState(0);

  useEffect(() => {
    api.get(`/quizzes/${id}`)
      .then(res => {
        setQuiz(res.data);
        setStartTime(Date.now());
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSelect = (qId, optionKey) => {
    setAnswers(prev => ({ ...prev, [qId]: optionKey }));
  };

  const handleSubmit = () => {
    const elapsedSeconds = Math.round((Date.now() - startTime) / 1000);
    setSubmitting(true);
    api.post(`/quizzes/${id}/attempt`, {
      answers,
      completion_time_seconds: elapsedSeconds
    })
    .then(res => {
      // Navigate to results page
      navigate(`/quizzes/${id}/result`);
    })
    .catch(err => {
      console.error(err);
      setSubmitting(false);
    });
  };

  if (loading) return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading assessment...</div>;
  if (!quiz) return null;

  const questions = quiz.questions || [];
  const currentQ = questions[currentIdx];
  const answeredCount = Object.keys(answers).length;
  const progressPct = (answeredCount / questions.length) * 100;
  const isLast = currentIdx === questions.length - 1;

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
            {quiz.module} • {quiz.topic}
          </div>
          <span className={`badge ${quiz.difficulty === 'advanced' ? 'badge-low' : quiz.difficulty === 'intermediate' ? 'badge-medium' : 'badge-high'}`} style={{ textTransform: 'capitalize' }}>
            {quiz.difficulty} Assessment
          </span>
        </div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '20px' }}>{quiz.title}</h1>
        
        {/* Progress Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ flex: 1, height: '6px', backgroundColor: 'var(--bg-input)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${progressPct}%`, height: '100%', backgroundColor: 'var(--accent-blue)', transition: 'width 0.3s ease' }} />
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            {answeredCount} / {questions.length}
          </div>
        </div>
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="glass-panel fade-in" key={currentIdx} style={{ padding: '36px' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '16px', fontWeight: 600 }}>
            Question {currentIdx + 1} of {questions.length}
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, lineHeight: 1.5, marginBottom: '24px' }}>
            {currentQ.question}
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {['a', 'b', 'c', 'd'].map(optKey => {
              const optText = currentQ[`option_${optKey}`];
              if (!optText) return null;
              
              const isSelected = answers[currentQ.id] === optKey;
              
              return (
                <button
                  key={optKey}
                  className="quiz-option-btn"
                  onClick={() => handleSelect(currentQ.id, optKey)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '16px',
                    padding: '16px', borderRadius: 'var(--radius-sm)',
                    backgroundColor: isSelected ? 'rgba(59,130,246,0.1)' : 'var(--bg-input)',
                    border: isSelected ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                    color: isSelected ? 'white' : 'var(--text-main)',
                    cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s ease',
                    width: '100%',
                    transform: isSelected ? 'translateY(-2px)' : 'none',
                    boxShadow: isSelected ? '0 4px 12px rgba(59,130,246,0.15)' : 'none'
                  }}
                >
                  <div style={{
                    width: '24px', height: '24px', borderRadius: '50%',
                    border: isSelected ? 'none' : '2px solid var(--text-dim)',
                    backgroundColor: isSelected ? 'var(--accent-blue)' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                  }}>
                    {isSelected && <CheckCircle size={14} color="white" />}
                  </div>
                  <span style={{ fontSize: '0.95rem', lineHeight: 1.4 }}>{optText}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
        <button
          onClick={() => setCurrentIdx(prev => Math.max(0, prev - 1))}
          disabled={currentIdx === 0}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: currentIdx === 0 ? 0.5 : 1 }}
        >
          <ChevronLeft size={16} /> Previous
        </button>

        {!isLast ? (
          <button
            onClick={() => setCurrentIdx(prev => Math.min(questions.length - 1, prev + 1))}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            Next <ChevronRight size={16} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting || answeredCount < questions.length}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: answeredCount === questions.length ? '#10b981' : 'var(--text-muted)' }}
          >
            {submitting ? 'Submitting...' : 'Submit Assessment'} <CheckCircle size={16} />
          </button>
        )}
      </div>
    </div>
  );
};

export default QuizPage;
