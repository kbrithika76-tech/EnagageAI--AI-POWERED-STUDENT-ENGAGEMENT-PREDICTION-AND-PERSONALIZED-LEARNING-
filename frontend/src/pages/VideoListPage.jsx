import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { PlayCircle, Clock, CheckCircle, BookOpen, ChevronDown, ChevronRight } from 'lucide-react';

const VideoListPage = () => {
  const [videos, setVideos] = useState([]);
  const [courses, setCourses] = useState([]);
  const [courseDetails, setCourseDetails] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedModules, setExpandedModules] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [videosRes, coursesRes] = await Promise.all([
          api.get('/content/videos'),
          api.get('/courses/')
        ]);
        setVideos(videosRes.data);
        setCourses(coursesRes.data);

        // Fetch details for each course (modules/concepts)
        const details = {};
        await Promise.all(
          coursesRes.data.map(async (course) => {
            try {
              const detailRes = await api.get(`/courses/${course.id}`);
              details[course.id] = detailRes.data;
            } catch (err) {
              console.error(`Failed to load course ${course.id}`, err);
            }
          })
        );
        setCourseDetails(details);

        // Expand all modules by default
        const expanded = {};
        Object.values(details).forEach(course => {
          (course.modules || []).forEach(m => {
            expanded[m.id] = true;
          });
        });
        setExpandedModules(expanded);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const toggleModule = (moduleId) => {
    setExpandedModules(prev => ({ ...prev, [moduleId]: !prev[moduleId] }));
  };

  if (loading) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading video lessons...</div>;
  }

  // Build a map of concept_id -> video[]
  const videosByConceptId = {};
  videos.forEach(v => {
    const cid = v.concept_id;
    if (cid) {
      if (!videosByConceptId[cid]) videosByConceptId[cid] = [];
      videosByConceptId[cid].push(v);
    }
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Video Lessons</h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Interactive video content organized by course and topic.
        </p>
      </div>

      {courses.map(course => {
        const detail = courseDetails[course.id];
        if (!detail) return null;
        const modules = detail.modules || [];

        // Count total videos in this course
        let courseVideoCount = 0;
        modules.forEach(m => {
          (m.concepts || []).forEach(c => {
            courseVideoCount += (videosByConceptId[c.id] || []).length;
          });
        });

        if (courseVideoCount === 0) return null;

        return (
          <div key={course.id}>
            {/* Course Heading */}
            <div style={{
              padding: '20px 24px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(139,92,246,0.08) 100%)',
              border: '1px solid rgba(59,130,246,0.15)',
              marginBottom: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                <BookOpen size={22} color="var(--accent-blue)" />
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {course.title}
                </h2>
                <span style={{
                  fontSize: '0.72rem',
                  padding: '2px 10px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(59,130,246,0.15)',
                  color: 'var(--accent-blue)',
                  fontWeight: 600
                }}>
                  {courseVideoCount} video{courseVideoCount !== 1 ? 's' : ''}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginLeft: '34px' }}>
                {course.description || `Explore ${course.title} video lessons.`}
              </p>
            </div>

            {/* Modules */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingLeft: '8px' }}>
              {modules.map(mod => {
                // Count videos in this module
                let modVideoCount = 0;
                (mod.concepts || []).forEach(c => {
                  modVideoCount += (videosByConceptId[c.id] || []).length;
                });
                if (modVideoCount === 0) return null;

                const isExpanded = expandedModules[mod.id];

                return (
                  <div key={mod.id}>
                    {/* Module Header */}
                    <div
                      onClick={() => toggleModule(mod.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-card)',
                        border: '1px solid var(--border-color)',
                        cursor: 'pointer',
                        userSelect: 'none',
                        marginBottom: isExpanded ? '12px' : '0'
                      }}
                    >
                      {isExpanded
                        ? <ChevronDown size={16} color="var(--accent-blue)" />
                        : <ChevronRight size={16} color="var(--text-muted)" />
                      }
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)' }}>
                        {mod.title}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginLeft: 'auto' }}>
                        {modVideoCount} video{modVideoCount !== 1 ? 's' : ''}
                      </span>
                    </div>

                    {/* Concepts & Videos inside module */}
                    {isExpanded && (
                      <div style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {(mod.concepts || []).map(concept => {
                          const conceptVideos = videosByConceptId[concept.id] || [];
                          if (conceptVideos.length === 0) return null;

                          return (
                            <div key={concept.id}>
                              {/* Concept Label */}
                              <div style={{
                                fontSize: '0.78rem',
                                fontWeight: 600,
                                color: 'var(--text-muted)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                                marginBottom: '8px',
                                paddingLeft: '4px'
                              }}>
                                {concept.title}
                              </div>

                              {/* Video Cards */}
                              <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                                gap: '16px'
                              }}>
                                {conceptVideos.map(v => {
                                  const prog = v.user_progress || {};
                                  const isDone = prog.is_completed;
                                  const pct = Math.round((prog.completion_pct || 0) * 100);

                                  return (
                                    <div
                                      key={v.id}
                                      className="glass-panel"
                                      style={{
                                        overflow: 'hidden',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        cursor: 'pointer',
                                        transition: 'transform 0.2s ease, border-color 0.2s ease'
                                      }}
                                      onClick={() => navigate(`/videos/${v.id}`)}
                                    >
                                      {/* Thumbnail */}
                                      <div style={{ position: 'relative', height: '160px', backgroundColor: '#1e293b' }}>
                                        <img
                                          src={v.thumbnail_url || 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=500&auto=format&fit=crop&q=60'}
                                          alt={v.title}
                                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        />
                                        <div style={{
                                          position: 'absolute',
                                          inset: 0,
                                          backgroundColor: 'rgba(0,0,0,0.3)',
                                          display: 'flex',
                                          alignItems: 'center',
                                          justifyContent: 'center'
                                        }}>
                                          <PlayCircle size={44} color="white" style={{ filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.5))' }} />
                                        </div>
                                        {isDone && (
                                          <div style={{ position: 'absolute', top: '10px', right: '10px' }} className="badge badge-high">
                                            <CheckCircle size={12} /> Completed
                                          </div>
                                        )}
                                      </div>

                                      {/* Info */}
                                      <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                                        <div>
                                          <span className="badge badge-medium" style={{ marginBottom: '6px' }}>{v.difficulty}</span>
                                          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '6px' }}>{v.title}</h3>
                                          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                            {v.description}
                                          </p>
                                        </div>

                                        <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <Clock size={12} /> {Math.round((v.duration_seconds || 300) / 60)} mins
                                          </span>
                                          <span>{pct}% watched</span>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default VideoListPage;
