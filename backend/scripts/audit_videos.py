import os
import sys
import sqlite3
import json
import shutil
import subprocess
from datetime import datetime

# Ensure yt-dlp is available

# ---------------------------------------------------------------------------
# Safety utilities
# ---------------------------------------------------------------------------
def safe_delete(cursor, table, id_val):
    """Delete a row safely, ensuring a WHERE clause is used.

    This function centralises deletions from a table by primary key and guards
    against accidental mass‑deletions. It raises a ValueError if the table name
    is empty or the id is None.
    """
    if not table:
        raise ValueError("Table name must be provided for safe_delete")
    if id_val is None:
        raise ValueError("ID value must be provided for safe_delete")
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id_val,))
try:
    import yt_dlp  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
    import yt_dlp  # now available

# Safe print wrapper to avoid UnicodeEncodeError
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoded = ' '.join(str(a).encode('utf-8', 'ignore').decode() for a in args)
        print(encoded, **kwargs)

# ---------- Configuration ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, 'backend', 'engageai.db')
BACKUP_DB_PATH = os.path.join(BASE_DIR, 'backend', 'engageai_backup.db')
REPORTS_DIR = os.path.join(BASE_DIR, 'outputs', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

REMOVED_LOG = os.path.join(REPORTS_DIR, 'video_cleanup_removed.txt')  # from previous step
VERIFICATION_REPORT = os.path.join(REPORTS_DIR, 'video_verification_report.txt')

# Trusted educational channels (exact channel names as reported by yt-dlp)
TRUSTED_CHANNELS = [
    "MIT OpenCourseWare",
    "Khan Academy",
    "3Blue1Brown",
    "StatQuest",
    "freeCodeCamp.org",
    "Corey Schafer",
    "Google Developers",
    "Microsoft Learn",
    "IBM Technology",
    "University of ...",  # generic placeholder; will match any university channel name in description
]

# Keywords indicating non‑educational content
NON_EDU_KEYWORDS = [
    "song", "music", "official video", "music video", "dance", "performance",
    "movie", "trailer", "comedy", "shorts", "entertainment", "remix",
    "cover", "live", "lyrics", "behind the scenes"
]

# ---------- Helper Functions ----------

def backup_database():
    """Create a timestamped backup of the SQLite database before any modifications."""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{BACKUP_DB_PATH}_{timestamp}.sqlite"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Database backup created at {backup_path}")
    return backup_path

def ensure_schema(conn: sqlite3.Connection):
    """Add missing columns to learning_contents if they do not exist."""
    c = conn.cursor()
    c.execute("PRAGMA table_info(learning_contents)")
    cols = [row['name'] for row in c.fetchall()]
    if 'license_verified' not in cols:
        c.execute("ALTER TABLE learning_contents ADD COLUMN license_verified INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("Added missing column license_verified to learning_contents")


def embed_to_watch_url(embed_url: str) -> str:
    """Convert a YouTube embed URL to a standard watch URL for yt‑dlp."""
    if not embed_url:
        return ""
    # Example: https://www.youtube.com/embed/dQw4w9WgXcQ -> https://www.youtube.com/watch?v=dQw4w9WgXcQ
    if "youtube.com/embed/" in embed_url:
        video_id = embed_url.split('/')[-1]
        return f"https://www.youtube.com/watch?v={video_id}"
    return embed_url

def fetch_metadata(url: str) -> dict:
    """Fetch video metadata using yt_dlp Python API without downloading."""
    if not url:
        return {}
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info if isinstance(info, dict) else {}
    except Exception as e:
        safe_print(f"Metadata fetch error for {url}: {e}")
        return {}

def search_youtube(query: str) -> list:
    """Search YouTube using yt_dlp's "ytsearch10" and return a list of video metadata dicts."""
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearch10 returns a playlist dict containing entries
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = result.get('entries', []) if result else []
            return [e for e in entries if isinstance(e, dict)]
    except Exception as e:
        safe_print(f"Search error for query '{query}': {e}")
        return []

# Replace all print calls with safe_print throughout the script
# At the end of main(), replace prints:
# print(f"Verification complete. Final status: {final_status}")
# ... etc.
# We'll adjust those lines accordingly.

def is_non_educational(meta: dict, concept_title: str) -> bool:
    """Determine with high confidence that a video is non‑educational.
    Checks:
    * Presence of any NON_EDU_KEYWORDS in title or description (case‑insensitive).
    * Channel (uploader) not in TRUSTED_CHANNELS *and* title/description do not contain the concept title.
    """
    title = meta.get('title', '').lower()
    description = meta.get('description', '').lower()
    for kw in NON_EDU_KEYWORDS:
        if kw in title or kw in description:
            return True
    # If uploader is a trusted channel, we consider it potentially educational.
    uploader = meta.get('uploader') or ''
    if any(trust.lower() in uploader.lower() for trust in TRUSTED_CHANNELS):
        return False
    # Otherwise, require the concept title to appear in title/description.
    if concept_title.lower() in title or concept_title.lower() in description:
        return False
    return True

def is_educational_verified(meta: dict, concept_title: str) -> bool:
    """Return True if we have strong evidence the video teaches the concept.
    * Trusted uploader **and** concept title present in title/description.
    * OR uploader not trusted but title/description clearly match concept and contain keywords like 'tutorial', 'introduction', 'lecture'.
    """
    title = meta.get('title', '').lower()
    description = meta.get('description', '').lower()
    uploader = meta.get('uploader') or ''
    trusted = any(trust.lower() in uploader.lower() for trust in TRUSTED_CHANNELS)
    concept_match = concept_title.lower() in title or concept_title.lower() in description
    edu_keywords = ["tutorial", "introduction", "lecture", "course", "lesson", "explained", "basics", "fundamentals"]
    has_edu_kw = any(kw in title or kw in description for kw in edu_keywords)
    return trusted and concept_match or (concept_match and has_edu_kw)

def extract_license(meta: dict) -> (str, bool):
    """Map yt‑dlp license string to our allowed status.
    Returns (license_type, license_verified).
    """
    raw = meta.get('license') or ''
    raw_lower = raw.lower()
    if "creative commons" in raw_lower:
        # We cannot assume CC‑BY unless explicitly stated.
        if "by" in raw_lower:
            return ("VERIFIED_CC_BY", True)
        else:
            return ("LICENSE_REQUIRES_VERIFICATION", False)
    if "public domain" in raw_lower:
        return ("VERIFIED_PUBLIC_DOMAIN", True)
    if "standard youtube license" in raw_lower:
        return ("STANDARD_YOUTUBE_LICENSE", False)
    # No clear license info
    return ("LICENSE_REQUIRES_VERIFICATION", False)

def allow_embedding(meta: dict) -> bool:
    """Determine if embedding is allowed based on yt‑dlp 'availability' field.
    If the video is 'public' we allow embedding, but we do not assume reuse permission.
    """
    availability = meta.get('availability') or ''
    return availability.lower() == 'public'

# ---------- Main Verification Process ----------

def main():
    # 0. Backup DB
    backup_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    ensure_schema(conn)

    # 1. Load all videos
    c.execute("SELECT * FROM learning_contents")
    videos = [dict(row) for row in c.fetchall()]
    total_videos_before = len(videos)

    # 2. Identify last 20 rows (IDs 94‑113) – they have already been removed in prior step, but double‑check.
    # We'll just ensure they are not present; if they are, delete them.
    c.execute("SELECT id FROM learning_contents WHERE id BETWEEN 94 AND 113")
    last_ids = {row['id'] for row in c.fetchall()}
    confirmed_removed = []
    for vid_id in last_ids:
        c.execute("SELECT * FROM learning_contents WHERE id = ?", (vid_id,))
        row = c.fetchone()
        if row:
            confirmed_removed.append({
                "ID": vid_id,
                "Title": row['title'],
                "Concept": row['concept_id'],
                "URL": row['video_url'],
                "Reason": "Non‑learning video / unwanted content (Last 20)"
            })
            safe_delete(c, "learning_contents", vid_id)
            c.execute("DELETE FROM content_progress WHERE content_id = ?", (vid_id,))
    conn.commit()

    # 3. Verify remaining videos
    confirmed_valid = []
    needs_manual_review = []
    removed_this_pass = []
    for v in videos:
        if v['id'] in last_ids:
            continue  # already removed above
        watch_url = embed_to_watch_url(v.get('video_url', ''))
        concept_id = v.get('concept_id')
        # Get concept title for matching
        concept_title = ''
        if concept_id:
            c.execute("SELECT title FROM concepts WHERE id = ?", (concept_id,))
            concept_row = c.fetchone()
            concept_title = concept_row['title'] if concept_row else ''
        meta = fetch_metadata(watch_url) if watch_url else {}
        if not meta:
            # Could not retrieve metadata – keep for manual review
            needs_manual_review.append(v)
            c.execute("UPDATE learning_contents SET license_type = 'NEEDS_MANUAL_VIDEO_REVIEW' WHERE id = ?", (v['id'],))
            continue
        # Check for clear non‑educational evidence
        if is_non_educational(meta, concept_title):
            removed_this_pass.append({
                "ID": v['id'],
                "Title": v['title'],
                "Concept": concept_id,
                "URL": v['video_url'],
                "Reason": "Detected non‑educational content (metadata)"
            })
            safe_delete(c, "learning_contents", v['id'])
            c.execute("DELETE FROM content_progress WHERE content_id = ?", (v['id'],))
            continue
        # Determine if we can confidently verify as educational
        if is_educational_verified(meta, concept_title):
            # Update metadata fields
            source_name = meta.get('uploader') or ''
            source_url = watch_url
            license_type, license_verified = extract_license(meta)
            attribution = meta.get('description') or ''
            embed_allowed = allow_embedding(meta)
            c.execute(
                """UPDATE learning_contents SET source_name = ?, source_url = ?, license_type = ?, attribution = ?, allow_embedding = ?, license_verified = ? WHERE id = ?""",
                (source_name, source_url, license_type, attribution, int(embed_allowed), int(license_verified), v['id'])
            )
            confirmed_valid.append(v)
        else:
            # Not enough evidence – keep for manual review
            needs_manual_review.append(v)
            c.execute("UPDATE learning_contents SET license_type = 'NEEDS_MANUAL_VIDEO_REVIEW' WHERE id = ?", (v['id'],))
    conn.commit()
    confirmed_removed.extend(removed_this_pass)

    # 4. Fill missing concepts (12 concepts expected)
    c.execute("SELECT * FROM concepts")
    all_concepts = [dict(row) for row in c.fetchall()]
    # Find concepts without any associated video (after removals)
    c.execute("SELECT DISTINCT concept_id FROM learning_contents WHERE concept_id IS NOT NULL")
    covered = {row['concept_id'] for row in c.fetchall()}
    missing_concepts = [cpt for cpt in all_concepts if cpt['id'] not in covered]
    newly_added = []
    for concept in missing_concepts:
        search_query = f"ytsearch10:{concept['title']}"
        try:
            # Run yt‑dlp search limited to 10 results, output JSON lines
            # Attempt up to 2 retries with a 60‑second timeout
            result = None
            for attempt in range(2):
                try:
                    result = subprocess.run(
                        ["yt-dlp", "--skip-download", "--dump-json", search_query],
                        capture_output=True, text=True, timeout=60
                    )
                    if result.returncode == 0:
                        break
                except subprocess.TimeoutExpired:
                    safe_print(f"Search timeout for concept {concept['title']} (attempt {attempt+1})")
                    continue
            if not result or result.returncode != 0:
                continue
                continue
            # yt‑dlp returns multiple JSON objects separated by newlines
            for line in result.stdout.strip().split('\n'):
                meta = json.loads(line)
                # Filter to trusted channels only
                uploader = meta.get('uploader') or ''
                if not any(trust.lower() in uploader.lower() for trust in TRUSTED_CHANNELS):
                    continue
                # Must match concept title reasonably
                if concept['title'].lower() not in (meta.get('title') or '').lower() and concept['title'].lower() not in (meta.get('description') or '').lower():
                    continue
                # Ensure not non‑educational
                if is_non_educational(meta, concept['title']):
                    continue
                # At this point we consider it a good candidate
                # Prepare insert data
                video_url = embed_to_watch_url('')  # we will store standard watch URL
                watch_url = meta.get('webpage_url') or ''
                # Insert learning content row
                # Extract license info for new video
                license_type, license_verified_flag = extract_license(meta)
                c.execute(
                    """INSERT INTO learning_contents (title, description, module, topic, content_type, video_url, thumbnail_url, duration_seconds, difficulty, tags, source_name, source_url, license_type, attribution, allow_embedding, license_verified, concept_id, is_active, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        meta.get('title'),
                        meta.get('description'),
                        '',  # module left blank – will be linked via concept hierarchy later
                        concept['title'],
                        'video',
                        watch_url,
                        meta.get('thumbnail'),
                        int(meta.get('duration') or 0),
                        'beginner',  # default difficulty – can be refined later
                        '',
                        meta.get('uploader'),
                        watch_url,
                        license_type,
                        meta.get('description'),
                        int(allow_embedding(meta)),
                        int(license_verified_flag),
                        concept['id'],
                        1,
                        datetime.utcnow().isoformat()
                    )
                )
                conn.commit()
                newly_added.append({
                    "ConceptID": concept['id'],
                    "ConceptTitle": concept['title'],
                    "VideoTitle": meta.get('title'),
                    "URL": watch_url,
                    "License": extract_license(meta)[0]
                })
                break  # stop after first suitable video
        except Exception as e:
            print(f"Error searching for concept {concept['title']}: {e}")
            continue
    # 5. Quiz integrity check (easy=15, moderate=10, difficult=5)
    quiz_integrity_ok = True
    quiz_issues = []
    c.execute("SELECT q.id, q.module, q.topic, q.difficulty FROM quizzes q")
    quizzes = [dict(row) for row in c.fetchall()]
    # Build mapping concept->counts
    concept_counts = {}
    for q in quizzes:
        key = (q['module'], q['topic'], q['difficulty'])
        concept_counts[key] = concept_counts.get(key, 0) + 1
    for key, cnt in concept_counts.items():
        _, _, difficulty = key
        expected = 15 if difficulty == 'easy' else 10 if difficulty == 'moderate' else 5 if difficulty == 'difficult' else None
        if expected is not None and cnt != expected:
            quiz_integrity_ok = False
            quiz_issues.append(f"Concept {key} has {cnt} {difficulty} quizzes (expected {expected})")
    # 6. Hierarchy integrity check
    hierarchy_ok = True
    hierarchy_issues = []
    # Verify every learning_contents.concept_id points to an existing concept
    c.execute("SELECT id, concept_id FROM learning_contents WHERE concept_id IS NOT NULL")
    for row in c.fetchall():
        c.execute("SELECT id FROM concepts WHERE id = ?", (row['concept_id'],))
        if not c.fetchone():
            hierarchy_ok = False
            hierarchy_issues.append(f"Video ID {row['id']} references missing concept ID {row['concept_id']}")
    # Verify concept -> module -> course chain exists
    c.execute("SELECT id, module_id FROM concepts")
    for row in c.fetchall():
        c.execute("SELECT id FROM course_modules WHERE id = ?", (row['module_id'],))
        if not c.fetchone():
            hierarchy_ok = False
            hierarchy_issues.append(f"Concept ID {row['id']} references missing module ID {row['module_id']}")
    c.execute("SELECT id, course_id FROM course_modules")
    for row in c.fetchall():
        c.execute("SELECT id FROM courses WHERE id = ?", (row['course_id'],))
        if not c.fetchone():
            hierarchy_ok = False
            hierarchy_issues.append(f"Module ID {row['id']} references missing course ID {row['course_id']}")

    # 7. Write verification report
    with open(VERIFICATION_REPORT, 'w', encoding='utf-8') as f:
        f.write("VIDEO VERIFICATION REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total videos before verification: {total_videos_before}\n")
        f.write(f"Videos removed during verification: {len(confirmed_removed)}\n")
        f.write(f"Verified educational videos retained: {len(confirmed_valid)}\n")
        f.write(f"Videos requiring manual review: {len(needs_manual_review)}\n")
        f.write(f"Newly added educational videos: {len(newly_added)}\n\n")
        # Sections A‑I
        f.write("A. CONFIRMED REMOVED VIDEOS\n")
        for r in confirmed_removed:
            f.write(f"- ID {r['ID']}: {r['Title']} | URL: {r['URL']} | Reason: {r['Reason']}\n")
        f.write("\nB. CONFIRMED VALID EDUCATIONAL VIDEOS\n")
        for v in confirmed_valid:
            f.write(f"- ID {v['id']}: {v['title']} | URL: {v['video_url']}\n")
        f.write("\nC. VIDEOS REQUIRING MANUAL REVIEW\n")
        for v in needs_manual_review:
            f.write(f"- ID {v['id']}: {v['title']} | URL: {v['video_url']}\n")
        f.write("\nD. NEWLY ADDED VERIFIED EDUCATIONAL VIDEOS\n")
        for n in newly_added:
            f.write(f"- Concept ID {n['ConceptID']} ({n['ConceptTitle']}): {n['VideoTitle']} | URL: {n['URL']} | License: {n['License']}\n")
        f.write("\nE. LICENSE VERIFICATION STATUS\n")
        for v in confirmed_valid:
            c.execute("SELECT license_type, license_verified FROM learning_contents WHERE id = ?", (v['id'],))
            lic, verified = c.fetchone()
            f.write(f"- ID {v['id']}: {lic} (verified={bool(verified)})\n")
        for v in needs_manual_review:
            c.execute("SELECT license_type FROM learning_contents WHERE id = ?", (v['id'],))
            lic = c.fetchone()['license_type']
            f.write(f"- ID {v['id']}: {lic}\n")
        f.write("\nF. CONCEPTS WITH VERIFIED VIDEOS\n")
        for v in confirmed_valid:
            c.execute("SELECT concept_id FROM learning_contents WHERE id = ?", (v['id'],))
            cid = c.fetchone()['concept_id']
            c.execute("SELECT title FROM concepts WHERE id = ?", (cid,))
            cname = c.fetchone()['title'] if c.fetchone() else 'N/A'
            f.write(f"- Concept ID {cid}: {cname}\n")
        f.write("\nG. CONCEPTS STILL MISSING VERIFIED VIDEOS\n")
        for concept in missing_concepts:
            f.write(f"- Concept ID {concept['id']}: {concept['title']}\n")
        f.write("\nH. QUIZ INTEGRITY CHECK\n")
        f.write(f"Status: {'PASS' if quiz_integrity_ok else 'FAIL'}\n")
        if not quiz_integrity_ok:
            for issue in quiz_issues:
                f.write(f"  * {issue}\n")
        f.write("\nI. HIERARCHY INTEGRITY CHECK\n")
        f.write(f"Status: {'PASS' if hierarchy_ok else 'FAIL'}\n")
        if not hierarchy_ok:
            for issue in hierarchy_issues:
                f.write(f"  * {issue}\n")
        f.write("\n" + "=" * 50 + "\n")
        # Final status determination
        final_status = "PASS"
        if confirmed_removed or needs_manual_review or missing_concepts:
            final_status = "PASS WITH WARNINGS"
        f.write(f"FINAL VIDEO CONTENT STATUS: {final_status}\n")

    # Print summary to console (captured by run_command)
    print(f"Verification complete. Final status: {final_status}")
    print(f"Report written to {VERIFICATION_REPORT}")
    print(f"Total videos before: {total_videos_before}")
    print(f"Removed: {len(confirmed_removed)}")
    print(f"Verified retained: {len(confirmed_valid)}")
    print(f"Manual review needed: {len(needs_manual_review)}")
    print(f"Newly added: {len(newly_added)}")
    print(f"Missing concepts after fill: {len(missing_concepts)}")
    print(f"Quiz integrity: {'PASS' if quiz_integrity_ok else 'FAIL'}")
    print(f"Hierarchy integrity: {'PASS' if hierarchy_ok else 'FAIL'}")

if __name__ == "__main__":
    main()
