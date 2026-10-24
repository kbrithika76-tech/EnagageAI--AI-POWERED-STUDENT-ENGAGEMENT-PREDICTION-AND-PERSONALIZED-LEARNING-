import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Users, Search, AlertCircle } from 'lucide-react';

const AdminStudentsPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get('/admin/users')
      .then(res => {
        // Filter only students
        setUsers(res.data.filter(u => u.role === 'student'));
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.patch(`/admin/users/${userId}/role`, { role: newRole });
      setUsers(prev => prev.filter(u => u.id !== userId)); // Remove if no longer a student
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = users.filter(u => 
    u.name.toLowerCase().includes(search.toLowerCase()) || 
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading students...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <Users color="#10b981" size={24} />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Student Management</h1>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Manage enrolled students, view system access, and promote to teachers if necessary.
        </p>
      </div>

      <div style={{ position: 'relative', maxWidth: '400px' }}>
        <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            width: '100%', padding: '10px 12px 10px 38px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--bg-input)',
            border: '1px solid var(--border-color)',
            color: 'white', outline: 'none', fontSize: '0.88rem'
          }}
        />
      </div>

      <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px' }}>ID</th>
              <th style={{ padding: '12px' }}>Student Name</th>
              <th style={{ padding: '12px' }}>Email</th>
              <th style={{ padding: '12px' }}>Joined Date</th>
              <th style={{ padding: '12px' }}>Change Role</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No students match your search.
                </td>
              </tr>
            ) : (
              filtered.map(u => (
                <tr key={u.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '12px' }}>#{u.id}</td>
                  <td style={{ padding: '12px', fontWeight: 600 }}>{u.name}</td>
                  <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{u.email}</td>
                  <td style={{ padding: '12px', color: 'var(--text-muted)' }}>
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      style={{
                        padding: '4px 8px', borderRadius: '4px',
                        backgroundColor: 'var(--bg-input)', color: 'white',
                        border: '1px solid var(--border-color)'
                      }}
                    >
                      <option value="student">Student</option>
                      <option value="teacher">Teacher</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminStudentsPage;
