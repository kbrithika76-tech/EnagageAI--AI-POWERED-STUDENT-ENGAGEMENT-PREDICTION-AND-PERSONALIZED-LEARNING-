import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldOff, ArrowLeft } from 'lucide-react';

const AccessRestrictedPage = () => {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at center, #1e1b4b 0%, #0b0f19 70%)',
      padding: '24px'
    }}>
      <div style={{ textAlign: 'center', maxWidth: '420px' }}>
        <div style={{
          width: '80px', height: '80px', borderRadius: '50%',
          background: 'rgba(244,63,94,0.12)',
          border: '2px solid rgba(244,63,94,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 24px'
        }}>
          <ShieldOff size={36} color="#f43f5e" />
        </div>

        <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '12px', color: '#fb7185' }}>
          🔒 Access Restricted
        </h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.7, marginBottom: '28px' }}>
          You don't have permission to access this workspace.<br />
          This area is restricted to authorized roles only.
        </p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button
            onClick={() => navigate(-1)}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <ArrowLeft size={16} /> Go Back
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-primary"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccessRestrictedPage;
