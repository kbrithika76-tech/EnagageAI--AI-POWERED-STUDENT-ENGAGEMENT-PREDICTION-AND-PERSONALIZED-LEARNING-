import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';

const Navbar = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  
  if (!user) return null;

  return (
    <header style={{
      height: '64px',
      backgroundColor: 'var(--bg-sidebar)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 28px'
    }}>
      <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
        Explainable AI Learning Analytics Dashboard
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <button
          onClick={toggleTheme}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        
        <span className="badge badge-high" style={{ textTransform: 'capitalize' }}>
          {user.role} Account
        </span>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          backgroundColor: 'var(--accent-blue)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
          fontSize: '0.85rem',
          color: 'white'
        }}>
          {user.name ? user.name[0].toUpperCase() : 'U'}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
