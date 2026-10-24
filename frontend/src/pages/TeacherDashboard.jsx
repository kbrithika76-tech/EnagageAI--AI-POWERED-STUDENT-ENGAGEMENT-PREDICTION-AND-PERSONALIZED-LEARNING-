import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../services/api';
import { Users, AlertTriangle, RefreshCw, Eye } from 'lucide-react';

const TeacherDashboard = () => {
  const location = useLocation();
  const isAtRiskPage = location.pathname === '/teacher/at-risk';
  const [students, setStudents] = useState([]);
  const [atRisk, setAtRisk] = useState([]);
  const [loading, setLoading] = useState(true);
  // CORRECTION 3: separate refreshing state so the table stays visible while refreshing
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState('');
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [inspecting, setInspecting] = useState(false);

  // Extracted fetch function so both initial load and the Refresh button can call it
  const fetchData = useCallback(async (isRefresh = false) => {
    setRefreshError('');
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [sRes, rRes] = await Promise.all([
        api.get('/teacher/students'),
        api.get('/teacher/at-risk'),
      ]);
      setStudents(sRes.data);
      setAtRisk(rRes.data);
      // Clear the selected student panel after refresh so it reflects updated data
      if (isRefresh) setSelectedStudent(null);
    } catch (err) {
      console.error(err);
      setRefreshError('Failed to refresh student data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData(false);
  }, [fetchData]);

  const handleInspectStudent = (studentId) => {
    setInspecting(true);
    api.get(`/teacher/students/${studentId}`)
      .then(res => setSelectedStudent(res.data))
      .catch(err => console.error(err))
      .finally(() => setInspecting(false));
  };

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading teacher dashboard...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header with Refresh Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>
            {isAtRiskPage ? 'At-Risk Alerts' : 'Teacher & Instructor Dashboard'}
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {isAtRiskPage 
              ? 'Monitor students who may need academic attention based on recent learning activity and performance.'
              : 'Monitor student engagement levels and view learning insights.'}
          </p>
        </div>
        {/* CORRECTION 3: Refresh button */}
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap' }}
        >
          <RefreshCw size={15} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          {refreshing ? 'Refreshing...' : 'Refresh Student List'}
        </button>
      </div>

      {/* Refresh Error Banner */}
      {refreshError && (
        <div style={{
          padding: '10px 14px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#fb7185',
          fontSize: '0.85rem'
        }}>
          {refreshError}
        </div>
      )}

      {/* At Risk Summary Alert (Only on At-Risk Page) */}
      {isAtRiskPage && (
        <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #f43f5e' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <AlertTriangle color="#f43f5e" size={22} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fb7185' }}>At-Risk Learners Alert ({atRisk.length})</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {atRisk.length === 1 
              ? '1 student may need academic attention based on recent learning activity and performance.'
              : `${atRisk.length} students may need academic attention based on recent learning activity and performance.`}
          </p>
        </div>
      )}

      {/* Student List Table */}
      <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>
            {isAtRiskPage ? 'At-Risk Students' : 'Enrolled Students & Engagement Levels'}
          </h3>
          {refreshing && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Updating data...</span>
          )}
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px' }}>ID</th>
              <th style={{ padding: '12px' }}>Student Name</th>
              <th style={{ padding: '12px' }}>Email</th>
              <th style={{ padding: '12px' }}>Engagement Level</th>
              <th style={{ padding: '12px' }}>Confidence</th>
              <th style={{ padding: '12px' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {(isAtRiskPage ? atRisk : students).length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  {isAtRiskPage ? 'No students are currently flagged as at-risk.' : 'No students enrolled yet.'}
                </td>
              </tr>
            ) : (
              (isAtRiskPage ? atRisk : students).map(s => {
                const level = s.prediction?.engagement_level || 'Pending';
                const badgeClass = level === 'Pending'
                  ? 'badge badge-medium'
                  : `badge badge-${level.toLowerCase()}`;
                return (
                  <tr key={s.student_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px' }}>#{s.student_id}</td>
                    <td style={{ padding: '12px', fontWeight: 600 }}>{s.name}</td>
                    <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{s.email}</td>
                    <td style={{ padding: '12px' }}>
                      <span className={badgeClass}>{level}</span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      {s.prediction?.confidence ? `${Math.round(s.prediction.confidence * 100)}%` : 'N/A'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button
                        onClick={() => handleInspectStudent(s.student_id)}
                        disabled={inspecting}
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Eye size={14} /> View Learning Insights
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Learning Insights Student Inspection Panel */}
      {inspecting && (
        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading learning insights...
        </div>
      )}

      {selectedStudent && !inspecting && (
        <div className="glass-panel" style={{ padding: '24px', border: '1px solid var(--accent-blue)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Learning Insights: {selectedStudent.student.name} (#{selectedStudent.student.id})
            </h3>
            <button
              onClick={() => setSelectedStudent(null)}
              style={{ background: 'none', color: 'var(--text-muted)', fontSize: '0.8rem' }}
            >
              ✕ Close
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', fontSize: '0.85rem' }}>
            <div>
              <p><strong>Predicted Engagement:</strong> {selectedStudent.prediction.engagement_level || 'Insufficient Activity'}</p>
              <p style={{ marginTop: '6px' }}><strong>Total Activity Events:</strong> {selectedStudent.stats.total_events}</p>
              <p style={{ marginTop: '6px' }}><strong>Completed Quizzes:</strong> {selectedStudent.stats.completed_quizzes}</p>
              <p style={{ marginTop: '6px' }}><strong>Avg Quiz Score:</strong> {selectedStudent.stats.avg_quiz_score}%</p>
            </div>
            <div>
              <p><strong>Key Learning Factors:</strong></p>
              <ul style={{ paddingLeft: '20px', color: '#34d399', marginTop: '4px' }}>
                {selectedStudent.explanation?.shap?.top_positive_features?.slice(0, 3).map((f, i) => (
                  <li key={i}>{f.display_name} (+{f.shap_value})</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherDashboard;
