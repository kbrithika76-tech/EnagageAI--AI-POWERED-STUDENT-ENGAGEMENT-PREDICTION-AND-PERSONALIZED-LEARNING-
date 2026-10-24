import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { BrainCircuit, ArrowRight } from 'lucide-react';

const OnboardingPage = () => {
  const [profile, setProfile] = useState({
    gender: 'M',
    region: 'South East Region',
    highest_education: 'A Level or Equivalent',
    imd_band: '50-60%',
    age_band: '0-35',
    disability: 'N',
    studied_credits: 60,
    num_of_prev_attempts: 0
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // Save profile to backend
      await api.put('/students/me/profile', profile);
      // Mark onboarding as done in localStorage so ProtectedLayout won't redirect again
      localStorage.setItem('engageai_onboarding_done', 'true');
      // Refresh global user state so profile.gender is now populated
      await refreshUser();
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      setError('Failed to save profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '520px', padding: '36px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <BrainCircuit size={36} color="#3b82f6" style={{ marginBottom: '8px' }} />
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Complete Student Onboarding Profile</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Provide background details to calibrate the 70-feature static branch of the Bi-LSTM model.
          </p>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.85rem',
            marginBottom: '12px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Highest Education Level</label>
            <select
              value={profile.highest_education}
              onChange={e => setProfile({ ...profile, highest_education: e.target.value })}
              style={{ width: '100%', padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-input)', color: 'white', border: '1px solid var(--border-color)', marginTop: '4px' }}
            >
              <option value="A Level or Equivalent">A Level or Equivalent</option>
              <option value="HE Qualification">HE Qualification</option>
              <option value="Lower Than A Level">Lower Than A Level</option>
              <option value="No Formal quals">No Formal Qualifications</option>
              <option value="Post Graduate Qualification">Post Graduate Qualification</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Gender</label>
              <select
                value={profile.gender}
                onChange={e => setProfile({ ...profile, gender: e.target.value })}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-input)', color: 'white', border: '1px solid var(--border-color)', marginTop: '4px' }}
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Age Band</label>
              <select
                value={profile.age_band}
                onChange={e => setProfile({ ...profile, age_band: e.target.value })}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', backgroundColor: 'var(--bg-input)', color: 'white', border: '1px solid var(--border-color)', marginTop: '4px' }}
              >
                <option value="0-35">0 - 35 Years</option>
                <option value="35-55">35 - 55 Years</option>
                <option value="55<=">55+ Years</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            {loading ? 'Saving Profile...' : 'Complete Profile & Start Learning'}
            <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default OnboardingPage;
