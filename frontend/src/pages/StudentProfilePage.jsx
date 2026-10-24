import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { User, Mail, GraduationCap, MapPin, BookOpen, Save, CheckCircle } from 'lucide-react';

const EDUCATION_OPTIONS = [
  'No Formal Quals', 'Lower Than A Level', 'A Level or Equivalent',
  'HE Qualification', 'Post Graduate Qualification'
];
const REGION_OPTIONS = [
  'East Anglian Region', 'East Midlands Region', 'London Region',
  'North Region', 'North Western Region', 'Scotland', 'South East Region',
  'South Region', 'South West Region', 'Wales', 'West Midlands Region', 'Yorkshire Region'
];
const AGE_OPTIONS = ['0-35', '35-55', '55<='];
const IMD_OPTIONS = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'];

const StudentProfilePage = () => {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState({
    gender: '', region: '', highest_education: '',
    imd_band: '', age_band: '', disability: 'N',
    studied_credits: 60, num_of_prev_attempts: 0
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.profile) {
      setProfile(p => ({ ...p, ...user.profile }));
    }
  }, [user]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await api.put('/students/me/profile', profile);
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError('Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const Field = ({ label, children }) => (
    <div>
      <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
        {label}
      </label>
      {children}
    </div>
  );

  const selectStyle = {
    width: '100%', padding: '10px 12px',
    borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--bg-input)',
    border: '1px solid var(--border-color)',
    color: 'white', outline: 'none', fontSize: '0.88rem'
  };

  const inputStyle = { ...selectStyle };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '720px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          width: '64px', height: '64px', borderRadius: '50%',
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1.6rem', flexShrink: 0
        }}>
          {user?.name?.charAt(0)?.toUpperCase() || '?'}
        </div>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>{user?.name}</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {user?.email} &nbsp;·&nbsp;
            <span className="badge badge-high" style={{ fontSize: '0.7rem' }}>Student</span>
          </p>
        </div>
      </div>

      {/* Profile Form */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <GraduationCap size={20} color="var(--accent-blue)" />
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Academic Profile</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
            Used by the Bi-LSTM model's 70-feature static branch
          </span>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px', borderRadius: 'var(--radius-sm)',
            backgroundColor: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)',
            color: '#fb7185', fontSize: '0.85rem', marginBottom: '16px'
          }}>{error}</div>
        )}

        <form onSubmit={handleSave} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <Field label="Gender">
            <select value={profile.gender || ''} onChange={e => setProfile(p => ({ ...p, gender: e.target.value }))} style={selectStyle}>
              <option value="">Select gender</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </Field>

          <Field label="Age Band">
            <select value={profile.age_band || ''} onChange={e => setProfile(p => ({ ...p, age_band: e.target.value }))} style={selectStyle}>
              <option value="">Select age range</option>
              {AGE_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </Field>

          <Field label="Highest Education Level">
            <select value={profile.highest_education || ''} onChange={e => setProfile(p => ({ ...p, highest_education: e.target.value }))} style={selectStyle}>
              <option value="">Select education</option>
              {EDUCATION_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </Field>

          <Field label="Region">
            <select value={profile.region || ''} onChange={e => setProfile(p => ({ ...p, region: e.target.value }))} style={selectStyle}>
              <option value="">Select region</option>
              {REGION_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </Field>

          <Field label="IMD Band (Deprivation Index)">
            <select value={profile.imd_band || ''} onChange={e => setProfile(p => ({ ...p, imd_band: e.target.value }))} style={selectStyle}>
              <option value="">Select IMD band</option>
              {IMD_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </Field>

          <Field label="Disability">
            <select value={profile.disability || 'N'} onChange={e => setProfile(p => ({ ...p, disability: e.target.value }))} style={selectStyle}>
              <option value="N">No disability</option>
              <option value="Y">Has disability</option>
            </select>
          </Field>

          <Field label="Studied Credits">
            <input type="number" value={profile.studied_credits || 60} min={0} max={240}
              onChange={e => setProfile(p => ({ ...p, studied_credits: parseFloat(e.target.value) }))}
              style={inputStyle} />
          </Field>

          <Field label="Previous Attempts">
            <input type="number" value={profile.num_of_prev_attempts || 0} min={0} max={10}
              onChange={e => setProfile(p => ({ ...p, num_of_prev_attempts: parseFloat(e.target.value) }))}
              style={inputStyle} />
          </Field>

          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button type="submit" disabled={saving} className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 24px' }}>
              {saved ? <><CheckCircle size={16} /> Saved!</> : saving ? 'Saving...' : <><Save size={16} /> Save Profile</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StudentProfilePage;
