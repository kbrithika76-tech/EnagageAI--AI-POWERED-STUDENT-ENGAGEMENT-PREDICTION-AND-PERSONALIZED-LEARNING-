import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { ShieldCheck, Users, PlayCircle, HelpCircle, Activity } from 'lucide-react';

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/admin/users'),
      api.get('/admin/analytics')
    ])
      .then(([uRes, aRes]) => {
        setUsers(uRes.data);
        setAnalytics(aRes.data);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.patch(`/admin/users/${userId}/role`, { role: newRole });
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading admin console...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Admin System Console</h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Global user role management, system analytics, and model performance metrics.
        </p>
      </div>

      {/* Analytics Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <AdminCard title="Total Users" value={analytics?.user_counts?.total || 0} icon={<Users color="#3b82f6" />} />
        <AdminCard title="Enrolled Students" value={analytics?.user_counts?.students || 0} icon={<Users color="#10b981" />} />
        <AdminCard title="Video Lessons" value={analytics?.content_counts?.videos || 0} icon={<PlayCircle color="#f59e0b" />} />
        <AdminCard title="Activity Events" value={analytics?.content_counts?.activity_events || 0} icon={<Activity color="#8b5cf6" />} />
      </div>

      {/* Model Performance Verification */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '12px' }}>Verified System Performance</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', fontSize: '0.9rem' }}>
          <div style={{ backgroundColor: 'var(--bg-input)', padding: '12px', borderRadius: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Test Accuracy:</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#34d399' }}>
              {analytics?.model_performance_summary?.test_accuracy}
            </div>
          </div>
          <div style={{ backgroundColor: 'var(--bg-input)', padding: '12px', borderRadius: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Macro F1-Score:</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#60a5fa' }}>
              {analytics?.model_performance_summary?.macro_f1}
            </div>
          </div>
          <div style={{ backgroundColor: 'var(--bg-input)', padding: '12px', borderRadius: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Architecture:</span>
            <div style={{ fontSize: '0.8rem', fontWeight: 700 }}>
              {analytics?.model_performance_summary?.architecture}
            </div>
          </div>
        </div>
      </div>

      {/* User Management Table */}
      <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px' }}>User Role Management</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px' }}>ID</th>
              <th style={{ padding: '12px' }}>Name</th>
              <th style={{ padding: '12px' }}>Email</th>
              <th style={{ padding: '12px' }}>Current Role</th>
              <th style={{ padding: '12px' }}>Change Role</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '12px' }}>#{u.id}</td>
                <td style={{ padding: '12px', fontWeight: 600 }}>{u.name}</td>
                <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{u.email}</td>
                <td style={{ padding: '12px' }}>
                  <span className="badge badge-medium">{u.role}</span>
                </td>
                <td style={{ padding: '12px' }}>
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-input)',
                      color: 'white',
                      border: '1px solid var(--border-color)'
                    }}
                  >
                    <option value="student">Student</option>
                    <option value="teacher">Teacher</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const AdminCard = ({ title, value, icon }) => (
  <div className="glass-panel" style={{ padding: '18px', display: 'flex', alignItems: 'center', gap: '16px' }}>
    <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'var(--bg-input)' }}>
      {icon}
    </div>
    <div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{title}</div>
      <div style={{ fontSize: '1.3rem', fontWeight: 800, marginTop: '2px' }}>{value}</div>
    </div>
  </div>
);

export default AdminDashboard;
