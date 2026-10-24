import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { CheckCircle, PlayCircle, Lock, ChevronDown, ChevronUp } from 'lucide-react';

const CourseDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedModules, setExpandedModules] = useState({});

  useEffect(() => {
    api.get(`/courses/${id}`)
      .then(res => {
        setCourse(res.data);
        // Expand first module by default
        if (res.data.modules && res.data.modules.length > 0) {
          setExpandedModules({ [res.data.modules[0].id]: true });
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [id]);

  const toggleModule = (moduleId) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleId]: !prev[moduleId]
    }));
  };

  const handleConceptClick = (concept) => {
    if (concept.has_video) {
      navigate(`/videos/${concept.video_id}`);
    } else {
      // For now, if no video is available yet
      alert('Content is currently being prepared for this lesson.');
    }
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading syllabus...</div>;
  }

  if (!course) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Course not found.</div>;
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <span className={`badge ${course.difficulty === 'advanced' ? 'badge-high' : course.difficulty === 'intermediate' ? 'badge-medium' : 'badge-low'}`} style={{ textTransform: 'capitalize' }}>
            {course.difficulty}
          </span>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            {course.modules.length} Modules • {course.duration_estimate || 'Self-paced'}
          </span>
        </div>
        <h1 style={{ fontSize: '2.4rem', fontWeight: 800, marginBottom: '16px', letterSpacing: '-0.5px' }}>
          {course.title}
        </h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', lineHeight: 1.6, maxWidth: '800px' }}>
          {course.description}
        </p>
      </div>

      {/* Modules Syllabus */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {course.modules.map((module, index) => {
          const isExpanded = expandedModules[module.id];
          const isLocked = false; 

          return (
            <div key={module.id} className="glass-panel fade-in" style={{ overflow: 'hidden', animationDelay: `${index * 0.1}s` }}>
              {/* Module Header */}
              <div 
                style={{ 
                  padding: '20px 24px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  backgroundColor: isExpanded ? 'rgba(59,130,246,0.05)' : 'transparent',
                  opacity: isLocked ? 0.6 : 1
                }}
                onClick={() => !isLocked && toggleModule(module.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ 
                    width: '32px', height: '32px', borderRadius: '50%', 
                    backgroundColor: 'var(--bg-input)', display: 'flex', 
                    alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)'
                  }}>
                    {index + 1}
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>
                      {module.title}
                    </h3>
                    {module.learning_objectives && (
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {module.learning_objectives}
                      </div>
                    )}
                  </div>
                </div>
                
                <div style={{ color: 'var(--text-dim)' }}>
                  {isLocked ? <Lock size={20} /> : (isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />)}
                </div>
              </div>

              {/* Module Concepts (Lessons) */}
              {isExpanded && !isLocked && (
                <div style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '0 0 16px 0' }} />
                  
                  {module.concepts.length === 0 && (
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '8px 0' }}>
                      No lessons available in this module yet.
                    </div>
                  )}

                  {module.concepts.map((concept, cIndex) => (
                    <div 
                      key={concept.id}
                      onClick={() => handleConceptClick(concept)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '12px 16px', borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-input)', cursor: 'pointer',
                        transition: 'background-color 0.2s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-input)'}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        {concept.is_completed ? (
                          <CheckCircle size={18} color="#10b981" />
                        ) : (
                          <PlayCircle size={18} color={concept.has_video ? 'var(--accent-blue)' : 'var(--text-dim)'} />
                        )}
                        <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-main)' }}>
                          {cIndex + 1}. {concept.title}
                        </span>
                      </div>
                      
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: concept.has_video ? 'var(--accent-blue)' : 'var(--text-dim)' }}>
                        {concept.is_completed ? '✓ Completed' : (concept.has_video ? '▶ Start Learning' : 'Coming Soon')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CourseDetailPage;
