import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Plus, Edit2, Trash2, ShieldCheck, CheckCircle } from 'lucide-react';

const TeacherCoursesPage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({
    title: '', description: '', module: 'General', topic: '',
    video_url: '', thumbnail_url: '', duration_seconds: 300, difficulty: 'beginner',
    source_name: '', license_type: 'Original Content', attribution: '', source_url: '', allow_embedding: true
  });

  const licenses = [
    'Original Content',
    'Public Domain',
    'Creative Commons Attribution (CC BY)',
    'Creative Commons Attribution-ShareAlike (CC BY-SA)',
    'Licensed Content',
    'External Embed — License Requires Verification'
  ];

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = () => {
    setLoading(true);
    api.get('/content/videos')
      .then(res => setVideos(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  const handleOpenModal = (video = null) => {
    if (video) {
      setEditingId(video.id);
      setFormData({
        title: video.title || '', description: video.description || '', module: video.module || 'General', topic: video.topic || '',
        video_url: video.video_url || '', thumbnail_url: video.thumbnail_url || '', duration_seconds: video.duration_seconds || 300, difficulty: video.difficulty || 'beginner',
        source_name: video.source_name || '', license_type: video.license_type || 'Original Content', attribution: video.attribution || '', source_url: video.source_url || '', allow_embedding: video.allow_embedding ?? true
      });
    } else {
      setEditingId(null);
      setFormData({
        title: '', description: '', module: 'General', topic: '',
        video_url: '', thumbnail_url: '', duration_seconds: 300, difficulty: 'beginner',
        source_name: '', license_type: 'Original Content', attribution: '', source_url: '', allow_embedding: true
      });
    }
    setShowModal(true);
  };

  const handleSave = () => {
    if (formData.license_type.includes('Creative Commons') && !formData.attribution) {
      alert("Attribution is mandatory for Creative Commons content.");
      return;
    }

    const req = editingId 
      ? api.put(`/content/videos/${editingId}`, formData)
      : api.post('/content/videos', formData);

    req.then(() => {
      setShowModal(false);
      fetchVideos();
    }).catch(err => {
      console.error(err);
      alert("Failed to save content.");
    });
  };

  const handleDelete = (id) => {
    if(confirm("Are you sure you want to deactivate this video?")) {
      api.delete(`/content/videos/${id}`)
        .then(() => fetchVideos())
        .catch(err => console.error(err));
    }
  };

  if (loading && videos.length === 0) return <div style={{ padding: '40px' }}>Loading content...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Content Management</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Add and manage learning videos, tracking source and copyright information.</p>
        </div>
        <button onClick={() => handleOpenModal()} className="btn-primary" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Plus size={16} /> Add Video
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px' }}>Title</th>
              <th style={{ padding: '12px' }}>Module & Topic</th>
              <th style={{ padding: '12px' }}>License</th>
              <th style={{ padding: '12px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {videos.map(v => (
              <tr key={v.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '12px', fontWeight: 600 }}>{v.title}</td>
                <td style={{ padding: '12px' }}>
                  <div style={{ color: 'var(--text-muted)' }}>{v.module}</div>
                  <div style={{ fontSize: '0.75rem' }}>{v.topic}</div>
                </td>
                <td style={{ padding: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: v.license_type.includes('Creative Commons') || v.license_type === 'Original Content' || v.license_type === 'Public Domain' ? '#10b981' : '#f59e0b' }}>
                    <ShieldCheck size={14} /> {v.license_type}
                  </div>
                </td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  <button onClick={() => handleOpenModal(v)} style={{ background: 'none', color: 'var(--accent-blue)', cursor: 'pointer', padding: '4px 8px' }}>
                    <Edit2 size={16} />
                  </button>
                  <button onClick={() => handleDelete(v.id)} style={{ background: 'none', color: 'var(--accent-rose)', cursor: 'pointer', padding: '4px 8px' }}>
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="glass-panel" style={{ width: '600px', maxHeight: '90vh', overflowY: 'auto', padding: '32px' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '20px' }}>{editingId ? 'Edit Video' : 'Add New Video'}</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Title</label>
                <input type="text" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }} />
              </div>
              
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Module</label>
                  <input type="text" value={formData.module} onChange={e => setFormData({...formData, module: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Topic</label>
                  <input type="text" value={formData.topic} onChange={e => setFormData({...formData, topic: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }} />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Video URL (Embed)</label>
                <input type="text" value={formData.video_url} onChange={e => setFormData({...formData, video_url: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }} />
              </div>

              {/* Copyright Section */}
              <div style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}><ShieldCheck size={16} color="var(--accent-blue)" /> Copyright & License</h4>
                <div style={{ color: '#f59e0b', fontSize: '0.75rem', marginBottom: '12px' }}>
                  Only add videos you own, have permission to use, or are legally available under a license that permits embedding.
                </div>
                
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>License Type</label>
                  <select value={formData.license_type} onChange={e => setFormData({...formData, license_type: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }}>
                    {licenses.map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Source / Creator Name</label>
                    <input type="text" value={formData.source_name} onChange={e => setFormData({...formData, source_name: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Source URL</label>
                    <input type="text" value={formData.source_url} onChange={e => setFormData({...formData, source_url: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)' }} />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Attribution (Required for CC)</label>
                  <textarea value={formData.attribution} onChange={e => setFormData({...formData, attribution: e.target.value})} style={{ width: '100%', padding: '8px', borderRadius: '4px', backgroundColor: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border-color)', minHeight: '60px' }} />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
              <button onClick={() => setShowModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleSave} className="btn-primary">Save Video</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherCoursesPage;
