import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, PlayCircle, HelpCircle, TrendingUp, BrainCircuit,
  Sparkles, AlertTriangle, Users, ShieldCheck, LogOut,
  BookOpen, Search, Award, BarChart2, User, Zap
} from 'lucide-react';

const Sidebar = () => {
  const { user, logout } = useAuth();
  if (!user) return null;

  const role = user.role || 'student';

  return (
    <aside style={{
      width: '240px',
      backgroundColor: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      padding: '20px 12px',
      flexShrink: 0
    }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '0 8px 20px 8px', borderBottom: '1px solid var(--border-color)', marginBottom: '12px' }}>
        <div style={{
          width: '34px', height: '34px', borderRadius: '10px',
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: 'var(--shadow-glow)', flexShrink: 0
        }}>
          <BrainCircuit size={20} color="white" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 800, letterSpacing: '-0.5px' }} className="gradient-text">EngageAI</h2>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            {role} Portal
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>

        {/* ── STUDENT ───────────────────────────────────────────── */}
        {role === 'student' && (
          <>
            <SectionLabel label="Learning" />
            <NavItem to="/dashboard"     icon={<LayoutDashboard size={16} />} label="Dashboard" />
            <NavItem to="/my-learning"   icon={<BookOpen size={16} />}        label="My Learning" />
            <NavItem to="/courses"       icon={<Search size={16} />}          label="Courses" />
            <NavItem to="/videos"        icon={<PlayCircle size={16} />}      label="Videos" />
            <NavItem to="/quizzes"       icon={<HelpCircle size={16} />}      label="Quizzes" />

            <SectionLabel label="AI Insights" />
            <NavItem to="/prediction"    icon={<TrendingUp size={16} />}      label="Engagement Level" />
            <NavItem to="/explanation"   icon={<BrainCircuit size={16} />}    label="How Can I Improve?" />
            <NavItem to="/recommendations" icon={<Sparkles size={16} />}     label="Recommended Learning" />
            <NavItem to="/early-warning" icon={<AlertTriangle size={16} />}   label="Early Support" />

            <SectionLabel label="Progress" />
            <NavItem to="/progress"      icon={<BarChart2 size={16} />}       label="Progress" />
            <NavItem to="/achievements"  icon={<Award size={16} />}           label="Achievements" />
            <NavItem to="/profile"       icon={<User size={16} />}            label="Profile" />
          </>
        )}

        {/* ── TEACHER ───────────────────────────────────────────── */}
        {role === 'teacher' && (
          <>
            <SectionLabel label="Students" />
            <NavItem to="/teacher/dashboard"   icon={<Users size={16} />}       label="Students Monitor" />
            <NavItem to="/teacher/at-risk"     icon={<AlertTriangle size={16} />} label="At-Risk Alerts" />

            <SectionLabel label="AI Tools" />
            <NavItem to="/teacher/ai-insights" icon={<BrainCircuit size={16} />} label="Learning Insights" />

            <SectionLabel label="Content" />
            <NavItem to="/teacher/content"     icon={<PlayCircle size={16} />}  label="Manage Videos" />
            <NavItem to="/teacher/quizzes"     icon={<HelpCircle size={16} />}  label="Manage Quizzes" />
            <NavItem to="/courses"             icon={<Search size={16} />}      label="Browse Courses" />
          </>
        )}

        {/* ── ADMIN ─────────────────────────────────────────────── */}
        {role === 'admin' && (
          <>
            <SectionLabel label="Administration" />
            <NavItem to="/admin/dashboard"    icon={<ShieldCheck size={16} />}  label="Admin Console" />
            <NavItem to="/teacher/dashboard"  icon={<Users size={16} />}        label="Teacher View" />
            <NavItem to="/teacher/ai-insights" icon={<BrainCircuit size={16} />} label="Learning Insights" />
            <NavItem to="/dashboard"          icon={<LayoutDashboard size={16} />} label="Student Preview" />
            <NavItem to="/courses"            icon={<Search size={16} />}        label="Browse Courses" />
          </>
        )}
      </nav>

      {/* User Footer */}
      <div style={{
        padding: '12px 10px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '8px'
      }}>
        <div style={{ overflow: 'hidden' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user.name}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user.email}
          </div>
        </div>
        <button onClick={logout} style={{ background: 'none', color: 'var(--accent-rose)', padding: '6px', flexShrink: 0 }} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};

const SectionLabel = ({ label }) => (
  <div style={{
    fontSize: '0.62rem', fontWeight: 700, color: 'var(--text-dim)',
    textTransform: 'uppercase', letterSpacing: '0.8px',
    padding: '10px 10px 4px 10px'
  }}>
    {label}
  </div>
);

const NavItem = ({ to, icon, label }) => (
  <NavLink
    to={to}
    style={({ isActive }) => ({
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '9px 12px',
      borderRadius: 'var(--radius-sm)',
      fontSize: '0.85rem',
      fontWeight: 500,
      color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
      backgroundColor: isActive ? 'var(--bg-card-hover)' : 'transparent',
      borderLeft: isActive ? '3px solid var(--accent-blue)' : '3px solid transparent',
      transition: 'all 0.15s ease',
      textDecoration: 'none'
    })}
  >
    {icon}
    <span>{label}</span>
  </NavLink>
);

export default Sidebar;
