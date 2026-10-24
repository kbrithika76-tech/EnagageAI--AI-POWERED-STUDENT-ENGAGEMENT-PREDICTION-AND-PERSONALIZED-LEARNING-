import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { BookOpen, Clock, BarChart2 } from 'lucide-react';

const CoursesPage = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/courses/')
      .then(res => {
        setCourses(res.data);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading courses...</div>;
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '8px' }}>Courses</h1>
        <p style={{ color: 'var(--text-muted)' }}>Explore our comprehensive learning paths.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
        {courses.map((course, index) => (
          <div key={course.id} className="glass-panel fade-in" style={{ 
            padding: '24px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px',
            animationDelay: `${index * 0.1}s`,
            cursor: 'pointer'
          }}
          onClick={() => navigate(`/courses/${course.id}`)}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
          }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>{course.title}</h2>
              <span className={`badge ${course.difficulty === 'advanced' ? 'badge-high' : course.difficulty === 'intermediate' ? 'badge-medium' : 'badge-low'}`} style={{ textTransform: 'capitalize' }}>
                {course.difficulty}
              </span>
            </div>
            
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', flex: 1, margin: 0, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              {course.description}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <BookOpen size={14} />
                <span>{course.module_count} Modules</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} />
                <span>{course.duration_estimate || 'Self-paced'}</span>
              </div>
            </div>

            <div style={{ marginTop: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '8px', color: 'var(--text-muted)' }}>
                <span>Progress</span>
                <span style={{ fontWeight: 600 }}>{course.progress_pct || 0}% Complete</span>
              </div>
              <div style={{ height: '6px', backgroundColor: 'var(--bg-input)', borderRadius: '3px', overflow: 'hidden', marginBottom: '16px' }}>
                <div style={{ width: `${course.progress_pct || 0}%`, height: '100%', backgroundColor: 'var(--accent-blue)', transition: 'width 0.3s ease' }} />
              </div>
              <button className="btn-primary" style={{ width: '100%' }} onClick={(e) => {
                e.stopPropagation();
                navigate(`/courses/${course.id}`);
              }}>
                Continue Learning
              </button>
            </div>
          </div>
        ))}
        {courses.length === 0 && (
          <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-muted)', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius-lg)' }}>
            No courses available at the moment.
          </div>
        )}
      </div>
    </div>
  );
};

export default CoursesPage;
