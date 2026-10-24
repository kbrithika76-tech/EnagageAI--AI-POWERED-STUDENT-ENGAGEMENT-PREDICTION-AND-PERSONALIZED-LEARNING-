import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BrainCircuit, Lock, Mail, ArrowRight, Eye, EyeOff, Sparkles, TrendingUp, BookOpen } from 'lucide-react';
import { tracker } from '../services/ActivityTracker';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let userData;
      if (isRegister) {
        userData = await register(name, email, password, role);
        if (role === 'student') {
          localStorage.removeItem('engageai_onboarding_done');
        }
      } else {
        userData = await login(email, password);
        if (userData.profile && userData.profile.gender) {
          localStorage.setItem('engageai_onboarding_done', 'true');
        }
      }

      tracker.track('LOGIN', { metadata: { role: userData.role } });

      if (userData.role === 'teacher') {
        navigate('/teacher/dashboard');
      } else if (userData.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoUser = (demoEmail, demoRole) => {
    setEmail(demoEmail);
    setPassword('password123');
    setRole(demoRole);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      backgroundColor: 'var(--bg-dark)'
    }}>
      {/* LEFT SIDE - Brand & Features */}
      <div className="fade-in" style={{
        flex: 1,
        display: 'none',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '60px',
        background: 'radial-gradient(circle at top right, #1e1b4b 0%, #0b0f19 60%)',
        borderRight: '1px solid var(--border-color)',
        '@media (min-width: 900px)': { display: 'flex' }
      }}>
        <div style={{ maxWidth: '480px', margin: '0 auto' }}>
          <div style={{
            width: '56px', height: '56px', borderRadius: '16px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '24px', boxShadow: 'var(--shadow-glow)'
          }}>
            <BrainCircuit size={32} color="white" />
          </div>
          <h1 style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '16px', letterSpacing: '-1px' }}>
            Transforming <span className="gradient-text">Learning</span> with AI.
          </h1>
          <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', marginBottom: '40px', lineHeight: 1.5 }}>
            Welcome to EngageAI, the modern learning platform that adapts to you.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ padding: '10px', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '12px', color: '#60a5fa' }}>
                <Sparkles size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>Personalized Learning</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Content tailored to your pace.</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ padding: '10px', backgroundColor: 'rgba(139,92,246,0.1)', borderRadius: '12px', color: '#a78bfa' }}>
                <TrendingUp size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>Smart Engagement Insights</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Understand how you learn best.</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ padding: '10px', backgroundColor: 'rgba(16,185,129,0.1)', borderRadius: '12px', color: '#34d399' }}>
                <BookOpen size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>Learn at Your Own Pace</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Structured courses and videos.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT SIDE - Login Form */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        position: 'relative'
      }}>
        {/* Mobile Header (Hidden on Desktop) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '32px', '@media (min-width: 900px)': { display: 'none' } }}>
           <BrainCircuit size={28} color="var(--accent-blue)" />
           <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }} className="gradient-text">EngageAI</h1>
        </div>

        <div className="glass-panel fade-in" style={{
          width: '100%',
          maxWidth: '420px',
          padding: '40px',
          borderRadius: 'var(--radius-lg)'
        }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '8px' }}>
            {isRegister ? 'Create an Account' : 'Welcome back'}
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '32px' }}>
            {isRegister ? 'Start your personalized learning journey today.' : 'Please enter your details to sign in.'}
          </p>

          {error && (
            <div className="fade-in" style={{
              padding: '12px 16px', borderRadius: 'var(--radius-sm)',
              backgroundColor: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.2)',
              color: '#fb7185', fontSize: '0.85rem', marginBottom: '20px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {isRegister && (
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '8px' }}>Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Alex Johnson"
                  className="form-input"
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '8px' }}>Email</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  className="form-input"
                  style={{ paddingLeft: '40px' }}
                />
                <Mail size={18} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '8px' }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="form-input"
                  style={{ paddingLeft: '40px', paddingRight: '40px' }}
                />
                <Lock size={18} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', color: 'var(--text-dim)' }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {isRegister && (
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '8px' }}>Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="form-input"
                >
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{ padding: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '12px', width: '100%' }}
            >
              {loading ? 'Authenticating...' : (isRegister ? 'Create Account' : 'Sign In')}
              <ArrowRight size={18} />
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => setIsRegister(!isRegister)}
              style={{ background: 'none', color: 'var(--accent-blue)', fontWeight: 600, padding: '4px' }}
            >
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </div>
        </div>

        {/* Subtle Demo Logins Footer */}
        <div className="fade-in" style={{ 
          marginTop: '32px', 
          textAlign: 'center', 
          maxWidth: '420px', 
          width: '100%',
          backgroundColor: 'rgba(255,255,255,0.02)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '16px'
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Demo Access
          </div>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <button onClick={() => fillDemoUser('student@engageai.com', 'student')} style={{ fontSize: '0.75rem', padding: '6px 12px', borderRadius: '4px', backgroundColor: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>Student</button>
            <button onClick={() => fillDemoUser('teacher@engageai.com', 'teacher')} style={{ fontSize: '0.75rem', padding: '6px 12px', borderRadius: '4px', backgroundColor: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>Teacher</button>
            <button onClick={() => fillDemoUser('admin@engageai.com', 'admin')} style={{ fontSize: '0.75rem', padding: '6px 12px', borderRadius: '4px', backgroundColor: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>Admin</button>
          </div>
        </div>
      </div>
      
      {/* Media query for hiding left side on small screens */}
      <style>
        {`
          @media (max-width: 900px) {
            .fade-in:first-child { display: none !important; }
            .mobile-brand { display: flex !important; }
          }
          .mobile-brand { display: none; }
        `}
      </style>
    </div>
  );
};

export default LoginPage;
