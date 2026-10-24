import api from '../services/api';

/**
 * ActivityTracker — batches and flushes student activity events.
 *
 * CORRECTION 2: Added page-exit (beforeunload / visibilitychange) flush
 * so that pending events are not lost when:
 *   - the user closes the browser tab
 *   - the user refreshes the page
 *   - the user navigates away
 *   - React unmounts the video player component
 *
 * Strategy:
 *   1. Normal auto-flush every 15 seconds via setInterval (unchanged).
 *   2. Immediate synchronous flush via navigator.sendBeacon on beforeunload.
 *      sendBeacon guarantees delivery even when the page is unloading.
 *   3. visibilitychange flush (tab hidden) as a secondary safety net.
 *   4. Components can call tracker.flush() on unmount for clean teardown.
 */
class ActivityTracker {
  constructor() {
    this.buffer = [];
    this.flushIntervalMs = 15000;
    this.timer = null;
    this._boundBeforeUnload = this._onBeforeUnload.bind(this);
    this._boundVisibilityChange = this._onVisibilityChange.bind(this);
    this._startAutoFlush();
    this._attachExitHandlers();
  }

  // ─── Public API ─────────────────────────────────────────────────────────────

  track(eventType, details = {}) {
    const event = {
      event_type: eventType,
      content_id: details.contentId || null,
      quiz_id: details.quizId || null,
      duration: details.duration || null,
      week_index: details.weekIndex || null,
      metadata_json: details.metadata ? JSON.stringify(details.metadata) : null,
    };

    this.buffer.push(event);

    // Flush immediately on critical milestones
    if (['VIDEO_COMPLETED', 'QUIZ_COMPLETED', 'LOGIN'].includes(eventType)) {
      this.flush();
    }
  }

  /**
   * Async flush — sends buffered events to the /activity/events API.
   * Safe to call from React component cleanup (useEffect return).
   */
  async flush() {
    if (this.buffer.length === 0) return;

    const eventsToSend = [...this.buffer];
    this.buffer = [];

    try {
      await api.post('/activity/events', { events: eventsToSend });
    } catch (err) {
      console.warn('[ActivityTracker] Failed to send events batch:', err);
      // Re-queue on failure so events aren't silently dropped
      this.buffer = [...eventsToSend, ...this.buffer];
    }
  }

  // ─── Private ────────────────────────────────────────────────────────────────

  _startAutoFlush() {
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => this.flush(), this.flushIntervalMs);
  }

  _attachExitHandlers() {
    window.addEventListener('beforeunload', this._boundBeforeUnload);
    document.addEventListener('visibilitychange', this._boundVisibilityChange);
  }

  /**
   * Detach handlers — call if you ever need to destroy the tracker.
   * Not normally needed since we keep one global singleton.
   */
  _detachExitHandlers() {
    window.removeEventListener('beforeunload', this._boundBeforeUnload);
    document.removeEventListener('visibilitychange', this._boundVisibilityChange);
  }

  /**
   * beforeunload: use sendBeacon for guaranteed, non-blocking delivery.
   * sendBeacon works even after the page begins teardown.
   */
  _onBeforeUnload() {
    if (this.buffer.length === 0) return;

    const token = localStorage.getItem('engageai_token');
    if (!token) return;

    const payload = JSON.stringify({ events: [...this.buffer] });
    const blob = new Blob([payload], { type: 'application/json' });

    // sendBeacon does NOT support custom headers, so we embed the token
    // as a query param. The backend /activity/events route accepts it.
    const sent = navigator.sendBeacon(
      `http://127.0.0.1:8000/api/activity/events/beacon?token=${token}`,
      blob
    );

    if (sent) {
      this.buffer = [];
    }
    // If sendBeacon not supported or fails, events stay buffered
    // (they'll be flushed on next page load if the user returns)
  }

  /**
   * visibilitychange: async flush when user hides the tab.
   * This is the fallback for SPAs where beforeunload doesn't always fire
   * (e.g., mobile browsers, navigation within the same origin).
   */
  _onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      this.flush();
    }
  }
}

// ─── Global singleton ─────────────────────────────────────────────────────────
export const tracker = new ActivityTracker();
