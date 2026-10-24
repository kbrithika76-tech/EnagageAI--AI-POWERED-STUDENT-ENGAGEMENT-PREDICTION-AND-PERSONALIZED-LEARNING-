import React, { useState, useRef, useEffect } from 'react';
import { BrainCircuit, X, Send, Minimize2 } from 'lucide-react';
import api from '../services/api';

/**
 * AICoach — Floating chat assistant.
 * Fetches the student's current prediction/dashboard context once on open,
 * then generates contextual responses based on the selected quick-question
 * and the student's actual engagement level + stats.
 */
const QUICK_QUESTIONS = [
  'What should I study today?',
  'Why is my engagement low?',
  'How can I improve my quiz score?',
  'What should I learn next?',
  'Explain my progress.',
  'Am I doing well?'
];

const AICoach = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: 'coach', text: "👋 Hi! I'm EngageAI Coach. Ask me anything about your learning, progress, or engagement!" }
  ]);
  const [context, setContext] = useState({});
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const bottomRef = useRef(null);

  // Load context when first opened
  useEffect(() => {
    if (open && !context.loaded) {
      api.get('/students/me/dashboard')
        .then(res => {
          const { stats, prediction, student } = res.data;
          setContext({
            loaded: true,
            name: student?.name,
            level: prediction?.engagement_level,
            confidence: prediction?.confidence,
            completed_videos: stats?.completed_videos || 0,
            completed_quizzes: stats?.completed_quizzes || 0,
            avg_score: stats?.avg_quiz_score || 0,
            streak: 0
          });
        })
        .catch(() => setContext({ loaded: true }));
    }
  }, [open, context.loaded]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    setMessages(m => [...m, { from: 'user', text }]);
    setInput('');
    setThinking(true);

    try {
      const res = await api.post('/students/me/chat', {
        message: text,
        context: context
      });
      setMessages(m => [...m, { from: 'coach', text: res.data.response }]);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "AI assistance is currently unavailable. Please try again later.";
      setMessages(m => [...m, { from: 'coach', text: errorMsg }]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          position: 'fixed', bottom: '28px', right: '28px',
          width: '56px', height: '56px', borderRadius: '50%',
          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 8px 24px rgba(59,130,246,0.4)',
          zIndex: 1000, border: 'none', cursor: 'pointer',
          transition: 'transform 0.2s ease'
        }}
        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        title="EngageAI Coach"
      >
        {open ? <X size={24} color="white" /> : <BrainCircuit size={24} color="white" />}
      </button>

      {/* Chat Panel */}
      {open && (
        <div style={{
          position: 'fixed', bottom: '96px', right: '28px',
          width: '360px', maxHeight: '520px',
          borderRadius: 'var(--radius-lg)',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-active)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          display: 'flex', flexDirection: 'column',
          zIndex: 999,
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '14px 18px',
            background: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2))',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <BrainCircuit size={20} color="var(--accent-blue)" />
              <div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>EngageAI Coach</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Powered by your Bi-LSTM profile</div>
              </div>
            </div>
            <button onClick={() => setOpen(false)} style={{ background: 'none', color: 'var(--text-muted)' }}>
              <Minimize2 size={16} />
            </button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: m.from === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div style={{
                  maxWidth: '82%',
                  padding: '10px 14px',
                  borderRadius: m.from === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  backgroundColor: m.from === 'user' ? 'var(--accent-blue)' : 'var(--bg-input)',
                  color: 'var(--text-main)',
                  fontSize: '0.84rem',
                  lineHeight: 1.55
                }}>
                  {m.text}
                </div>
              </div>
            ))}
            {thinking && (
              <div style={{ display: 'flex', gap: '5px', padding: '8px 14px', width: 'fit-content' }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: '7px', height: '7px', borderRadius: '50%',
                    backgroundColor: 'var(--text-muted)',
                    animation: `bounce 1.2s ease infinite ${i * 0.2}s`
                  }} />
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick Questions */}
          <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {QUICK_QUESTIONS.slice(0, 3).map(q => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                style={{
                  padding: '4px 10px', borderRadius: '999px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-muted)', fontSize: '0.72rem', cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input */}
          <div style={{
            padding: '10px 12px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex', gap: '8px'
          }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage(input)}
              placeholder="Ask EngageAI Coach..."
              style={{
                flex: 1, padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
                color: 'white', outline: 'none', fontSize: '0.84rem'
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || thinking}
              className="btn-primary"
              style={{ padding: '8px 12px' }}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </>
  );
};

export default AICoach;
