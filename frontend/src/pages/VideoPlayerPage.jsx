import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { PlayCircle, Clock, BookOpen, ExternalLink, ShieldCheck, CheckCircle } from 'lucide-react';

const VideoPlayerPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [video, setVideo] = useState(null);
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [progressPct, setProgressPct] = useState(0);
  
  // Activity tracking refs
  const watchTimerRef = useRef(null);
  const watchSecondsRef = useRef(0);
  const maxWatchSecondsRef = useRef(0);
  const playerRef = useRef(null);
  const apiReadyRef = useRef(false); // true when YouTube IFrame API script has loaded
  const scriptLoadedRef = useRef(false); // ensures script is added only once
  const lastTimeRef = useRef(0); // tracks last known playback time for genuine progress

  useEffect(() => {
    Promise.all([
      api.get(`/content/videos/${id}`),
      api.get(`/content/videos/${id}/quizzes`)
    ])
    .then(([videoRes, quizzesRes]) => {
      setVideo(videoRes.data);
      setQuizzes(quizzesRes.data);
      
      // Restore previous progress
      const initialSeconds = videoRes.data.user_progress?.watch_seconds || 0;
      watchSecondsRef.current = initialSeconds;
      maxWatchSecondsRef.current = initialSeconds;
      setCompleted(videoRes.data.user_progress?.is_completed || false);
      
      const duration = videoRes.data.duration_seconds || 300;
      setProgressPct(Math.min(100, Math.round((initialSeconds / duration) * 100)));
    })
    .catch(err => console.error(err))
    .finally(() => setLoading(false));

    return () => {
      if (watchTimerRef.current) clearInterval(watchTimerRef.current);
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
      stopTrackingAndSave();
    };
  }, [id]);

  const getYouTubeVideoId = (url) => {
    if (!url) return null;
    const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^"&?\/\s]{11})/);
    return match ? match[1] : null;
  };

  const videoId = video ? getYouTubeVideoId(video.video_url) : null;
  const [iframeError, setIframeError] = useState(false);

  useEffect(() => {
  if (!videoId || iframeError || loading) return;

  const loadPlayer = () => {
    if (playerRef.current) return;
    playerRef.current = new window.YT.Player('yt-player-container', {
      videoId,
      host: 'https://www.youtube-nocookie.com',    // TOP-LEVEL: privacy-enhanced embed domain
      playerVars: {
        playsinline: 1,
        rel: 0,                                     // no related videos from other channels
        enablejsapi: 1,
        origin: window.location.origin,
        iv_load_policy: 3,                          // disable annotations / info cards
        playlist: videoId,                          // single-video playlist suppresses suggestions
        controls: 1,                                // keep standard player controls
        disablekb: 0,                               // keep keyboard shortcuts
        fs: 1,                                      // allow fullscreen
      },
      events: {
        onStateChange: onPlayerStateChange,
        onError: () => setIframeError(true),
      },
    });
  };

  if (!window.YT || !window.YT.Player) {
    if (!scriptLoadedRef.current) {
      scriptLoadedRef.current = true;
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
      window.onYouTubeIframeAPIReady = loadPlayer;
    }
  } else {
    loadPlayer();
  }
}, [videoId, iframeError, loading]);

  const onPlayerStateChange = (event) => {
    if (event.data === window.YT.PlayerState.PLAYING) {
      if (watchTimerRef.current) clearInterval(watchTimerRef.current);
      watchTimerRef.current = setInterval(trackProgress, 1000);
    } else if (event.data === window.YT.PlayerState.ENDED) {
      // Backup: if the video reaches ENDED, seek back and pause
      if (watchTimerRef.current) clearInterval(watchTimerRef.current);
      stopTrackingAndSave();
      try {
        const dur = playerRef.current?.getDuration();
        if (dur && dur > 2) {
          playerRef.current.seekTo(dur - 1, true);
          playerRef.current.pauseVideo();
        }
      } catch (e) { /* player may already be destroyed */ }
    } else {
      if (watchTimerRef.current) {
        clearInterval(watchTimerRef.current);
        stopTrackingAndSave();
      }
    }
  };

  const trackProgress = () => {
    watchSecondsRef.current += 1;
    maxWatchSecondsRef.current = Math.max(maxWatchSecondsRef.current, watchSecondsRef.current);
    
    const duration = playerRef.current?.getDuration() || video?.duration_seconds || 300;
    const currentPct = Math.min(100, Math.round((maxWatchSecondsRef.current / duration) * 100));
    setProgressPct(currentPct);
    
    if (currentPct >= 85) {
      setCompleted(true);
      // Backend automatically checks threshold and validates
    }

    // Proactively pause the video 2 seconds before it ends to prevent
    // YouTube's end-screen "More videos" overlay from ever appearing.
    // YouTube shows creator end-screens in the last 5-20 seconds, but
    // the overlay with clickable cards appears in the final seconds.
    try {
      const currentTime = playerRef.current?.getCurrentTime();
      if (currentTime && duration && (duration - currentTime) <= 2) {
        playerRef.current.pauseVideo();
        playerRef.current.seekTo(duration - 2, true);
        if (watchTimerRef.current) clearInterval(watchTimerRef.current);
        stopTrackingAndSave();
      }
    } catch (e) { /* ignore if player is not ready */ }
  };

  const stopTrackingAndSave = () => {
    if (watchTimerRef.current) clearInterval(watchTimerRef.current);
    const duration = playerRef.current?.getDuration() || video?.duration_seconds || 300;
    const payload = JSON.stringify({
      watch_seconds: maxWatchSecondsRef.current,
      duration_seconds: Math.floor(duration)
    });
    const token = localStorage.getItem('engageai_token');
    if (navigator.sendBeacon) {
      const blob = new Blob([payload], { type: 'application/json' });
      navigator.sendBeacon(`/api/content/videos/${id}/progress`, blob);
    } else {
      fetch(`/api/content/videos/${id}/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: payload,
        keepalive: true
      });
    }
  };

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
      Loading video content...
    </div>
  );

  if (!video) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Breadcrumb & Title */}
      <div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
          {video.module} • {video.topic}
        </div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>{video.title}</h1>
      </div>

      {/* Video Player Area */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', backgroundColor: '#0f172a' }}>
          {videoId && !iframeError ? (
            <div id="yt-player-container" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}></div>
          ) : (
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'white', padding: '20px', textAlign: 'center' }}>
              <div style={{ marginBottom: '16px', fontSize: '1.2rem', fontWeight: 'bold' }}>
                {iframeError ? 'Video unavailable for embedded playback' : 'Video link unavailable'}
              </div>

            </div>
          )}
        </div>
        
        {/* Source & License Info Box */}
        <div style={{ padding: '16px 24px', backgroundColor: 'var(--bg-input)', borderTop: '1px solid var(--border-color)', display: 'flex', flexWrap: 'wrap', gap: '24px', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={16} color="var(--accent-blue)" />
            <span style={{ color: 'var(--text-muted)' }}>License:</span>
            <span style={{ fontWeight: 600 }}>{video.license_type || 'External Embed'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={16} color="var(--accent-emerald)" />
            <span style={{ color: 'var(--text-muted)' }}>Source:</span>
            <span style={{ fontWeight: 600 }}>{video.source_name || 'Original Content'}</span>
          </div>
          {(video.attribution || video.source_url) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ExternalLink size={16} color="var(--text-dim)" />
              <span style={{ color: 'var(--text-muted)' }}>Attribution:</span>
              <a href={video.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>
                {video.attribution || 'View Original Source'}
              </a>
            </div>
          )}
        </div>
      </div>

      <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Description & Objectives */}
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', color: 'var(--text-main)' }}>About this lesson</h2>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            {video.description}
          </p>
          <div style={{ marginTop: '24px', padding: '16px', backgroundColor: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.1)', borderRadius: 'var(--radius-sm)' }}>
             <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '8px' }}>
               <BookOpen size={18} /> Learning Objectives
             </h4>
             <ul style={{ fontSize: '0.9rem', color: 'var(--text-muted)', margin: '12px 0 0 24px', lineHeight: 1.6 }}>
                <li>Understand the core principles of {video.topic}</li>
                <li>Apply this knowledge in practical scenarios</li>
             </ul>
          </div>
          <div style={{ marginTop: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {video.tags && video.tags.split(',').map(tag => (
              <span key={tag} style={{ padding: '6px 12px', backgroundColor: 'var(--bg-input)', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                #{tag.trim()}
              </span>
            ))}
          </div>
        </div>

        {/* Details & Progress */}
        <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '20px' }}>Lesson Status</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.95rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Difficulty</span>
              <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{video.difficulty}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Duration</span>
              <span style={{ fontWeight: 600 }}>{video.duration_seconds ? Math.round(video.duration_seconds / 60) + ' mins' : '—'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Status</span>
              {completed ? (
                <span style={{ color: '#10b981', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}><CheckCircle size={16}/> Completed</span>
              ) : (
                <span style={{ color: '#f59e0b', fontWeight: 700 }}>In Progress</span>
              )}
            </div>
          </div>
          <div style={{ marginTop: 'auto', paddingTop: '24px' }}>
            {completed ? (
              <div style={{ width: '100%', marginBottom: '12px', padding: '14px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', borderRadius: 'var(--radius-sm)', textAlign: 'center', fontWeight: 600 }}>
                <CheckCircle size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'text-bottom' }} /> ✓ Video Completed
              </div>
            ) : (
              <div style={{ width: '100%', marginBottom: '12px', padding: '14px', backgroundColor: 'var(--bg-input)', color: 'var(--text-muted)', borderRadius: 'var(--radius-sm)', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontWeight: 600 }}>Progress: {progressPct}%</span>
                <span style={{ fontSize: '0.85rem' }}>Watch {Math.max(0, 85 - progressPct)}% more to complete</span>
              </div>
            )}
            <button className="btn-primary" style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', padding: '14px' }} onClick={() => navigate('/courses')}>
              Next Lesson <PlayCircle size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Quizzes Section */}
      <div>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          Test Your Understanding
        </h2>
        {quizzes.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No quizzes available for this video yet.</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {quizzes.map(q => {
              const diffBadge = q.difficulty === 'advanced' ? 'badge-low' : q.difficulty === 'intermediate' ? 'badge-medium' : 'badge-high';
              const passed = q.user_attempt?.attempted && q.user_attempt.best_score_pct >= 50;
              
              return (
                <div key={q.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <span className={`badge ${diffBadge}`} style={{ textTransform: 'capitalize' }}>{q.difficulty}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{q.question_count} Questions</span>
                  </div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '8px', lineHeight: 1.3 }}>{q.title}</h3>
                  
                  <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
                    {q.user_attempt?.attempted ? (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: passed ? '#10b981' : '#f43f5e' }}>
                          Score: {q.user_attempt.best_score_pct}%
                        </span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button onClick={() => navigate(`/quizzes/${q.id}/result`)} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>Review</button>
                          <button onClick={() => navigate(`/quizzes/${q.id}`)} className="btn-primary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>Retake</button>
                        </div>
                      </div>
                    ) : (
                      <button onClick={() => navigate(`/quizzes/${q.id}`)} className="btn-primary" style={{ width: '100%' }}>
                        Start Quiz
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
};

export default VideoPlayerPage;
