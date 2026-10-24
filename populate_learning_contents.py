"""
populate_learning_contents.py
Populate the learning_contents table with verified educational videos
for existing concepts that currently lack a video.

Safety:
- Never deletes existing data
- Only INSERTs into learning_contents for concepts with no video
- Logs every added, rejected, and missing video
"""
import os
import sys
import sqlite3
import datetime
import time

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from youtubesearchpython import VideosSearch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'backend', 'engageai.db')
REPORT_PATH = os.path.join(BASE_DIR, 'outputs', 'reports', 'video_population_report.txt')

TRUSTED_CHANNELS = [
    "freecodecamp.org",
    "freecodecamp",
    "mit opencourseware",
    "khan academy",
    "3blue1brown",
    "statquest with josh starmer",
    "statquest",
    "corey schafer",
    "deeplearning.ai",
    "google developers",
    "microsoft developer",
    "microsoft learn",
    "ibm technology",
    "stanford",
    "harvard",
    "programming with mosh",
    "sentdex",
    "tech with tim",
    "edureka",
    "simplilearn",
    "krish naik",
    "codebasics",
    "campusx",
    "telusko",
    "bro code",
    "cs dojo",
    "clever programmer",
    "traversy media",
    "the coding train",
    "computerphile",
    "two minute papers",
    "deeplizard",
    "codewithharry",
    "neural nine",
    "techworld with nana",
    "fireship",
    "intellipaat",
    "great learning",
]

NON_EDU_KEYWORDS = [
    "song", "music video", "dance", "performance",
    "movie", "trailer", "comedy", "entertainment", "remix",
    "cover", "lyrics", "behind the scenes", "vlog", "funny", "meme",
    "gaming", "gameplay", "unboxing", "reaction", "prank",
]

EDU_KEYWORDS = [
    "tutorial", "introduction", "lecture", "course", "lesson",
    "explained", "basics", "fundamentals", "what is", "how to",
    "learn", "beginner", "overview", "deep dive", "walkthrough",
    "programming", "coding", "python", "neural", "machine learning",
]


def duration_to_seconds(duration_str):
    """Convert duration string like '12:34' or '1:02:03' to seconds."""
    if not duration_str:
        return 0
    parts = duration_str.split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            return int(parts[0])
    except ValueError:
        pass
    return 0


def is_confident_educational(video, concept_title):
    """Return True only if we are confident the video genuinely teaches the concept.
    
    Rules:
    1. Reject if title contains non-educational keywords
    2. Concept words must appear in title or description
    3. Must be from a trusted channel OR have educational keywords in title
    """
    title = video.get('title', '').lower()
    channel_info = video.get('channel', {})
    channel = channel_info.get('name', '').lower() if channel_info else ''
    
    # Build description from snippets
    desc_snippets = video.get('descriptionSnippet')
    if isinstance(desc_snippets, list):
        description = " ".join([s.get('text', '') for s in desc_snippets if isinstance(s, dict)]).lower()
    else:
        description = ""

    # 1. Reject if title contains non-edu keywords
    for kw in NON_EDU_KEYWORDS:
        if kw in title:
            return False

    # 2. Check concept relevance - concept words must appear in title or description
    concept_lower = concept_title.lower()
    concept_words = [w for w in concept_lower.split() if len(w) > 2]  # skip tiny words like "to", "and"
    
    # Check if concept title as a whole appears
    full_match = concept_lower in title or concept_lower in description
    
    # Or check if all significant words appear
    word_match = all(word in title or word in description for word in concept_words) if concept_words else False
    
    if not full_match and not word_match:
        return False

    # 3. Must be from trusted channel OR have educational keywords
    is_trusted = any(tc in channel for tc in TRUSTED_CHANNELS)
    has_edu_kw = any(kw in title for kw in EDU_KEYWORDS)
    
    return is_trusted or has_edu_kw


def search_videos(query, limit=10):
    """Search YouTube and return results, handling errors gracefully."""
    try:
        search = VideosSearch(query, limit=limit)
        results = search.result()
        return results.get('result', []) if results else []
    except Exception as e:
        return None, str(e)


def populate_videos():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ensure license_verified column exists
    cursor.execute("PRAGMA table_info(learning_contents)")
    cols = [row['name'] for row in cursor.fetchall()]
    if 'license_verified' not in cols:
        cursor.execute("ALTER TABLE learning_contents ADD COLUMN license_verified INTEGER NOT NULL DEFAULT 0")
        conn.commit()

    # Load concepts with their module and course context
    cursor.execute("""
        SELECT c.id as concept_id, c.title as concept_title, 
               m.title as module_title, cr.title as course_title
        FROM concepts c
        JOIN course_modules m ON c.module_id = m.id
        JOIN courses cr ON m.course_id = cr.id
        ORDER BY c.id
    """)
    concepts = cursor.fetchall()

    added_videos = []
    rejected_videos = []
    missing_concepts = []
    skipped_existing = 0

    total = len(concepts)
    for idx, concept in enumerate(concepts, 1):
        concept_id = concept['concept_id']
        concept_title = concept['concept_title'] or ''
        module_title = concept['module_title'] or ''
        course_title = concept['course_title'] or ''

        print(f"[{idx}/{total}] Processing concept {concept_id}: {concept_title}...", flush=True)

        # Skip if already has a video
        cursor.execute("SELECT id FROM learning_contents WHERE concept_id = ?", (concept_id,))
        if cursor.fetchone():
            skipped_existing += 1
            print(f"  -> Already has video, skipping.", flush=True)
            continue

        # Build search queries - try multiple strategies
        queries = []
        # Primary: course + concept + tutorial
        if course_title and concept_title:
            queries.append(f"{course_title} {concept_title} tutorial")
        # Secondary: module + concept + tutorial  
        if module_title and concept_title:
            queries.append(f"{module_title} {concept_title} tutorial")
        # Tertiary: just concept + programming/tutorial
        if concept_title:
            queries.append(f"{concept_title} programming tutorial")
            queries.append(f"{concept_title} explained")

        selected_video = None
        all_rejected = []

        for query in queries:
            result = search_videos(query)
            
            # Handle error case
            if isinstance(result, tuple):
                missing_concepts.append(f"Concept {concept_id}: {concept_title} - Search failed: {result[1]}")
                break
            
            if result is None:
                continue

            for video in result:
                if is_confident_educational(video, concept_title):
                    selected_video = video
                    break
                else:
                    all_rejected.append(f"Rejected '{video.get('title', '?')}' for concept '{concept_title}' (query: {query})")

            if selected_video:
                break
            
            # Small delay between searches to avoid rate limiting
            time.sleep(0.5)

        if selected_video:
            title = selected_video.get('title', '')
            url = selected_video.get('link', '')
            channel_info = selected_video.get('channel', {})
            channel = channel_info.get('name', '') if channel_info else ''
            duration = duration_to_seconds(selected_video.get('duration', '0'))
            thumbnails = selected_video.get('thumbnails', [])
            thumbnail_url = thumbnails[0].get('url', '') if thumbnails else ''

            license_type = "STANDARD_YOUTUBE_LICENSE"
            license_verified = 0

            try:
                cursor.execute("""
                    INSERT INTO learning_contents 
                    (title, description, module, topic, content_type, video_url, 
                     thumbnail_url, duration_seconds, difficulty, tags,
                     source_name, source_url, license_type, attribution, 
                     allow_embedding, license_verified, concept_id, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    title,  # description
                    module_title,  # module (NOT NULL)
                    concept_title,  # topic
                    'video',
                    url,
                    thumbnail_url,
                    duration,
                    'beginner',
                    '',  # tags
                    channel,
                    url,
                    license_type,
                    f"Video by {channel}",
                    1,  # allow_embedding
                    license_verified,
                    concept_id,
                    1,  # is_active
                    datetime.datetime.utcnow().isoformat(),
                ))
                conn.commit()
                added_videos.append({
                    'concept_id': concept_id,
                    'concept_title': concept_title,
                    'video_title': title,
                    'channel': channel,
                    'url': url,
                    'license': license_type,
                    'license_verified': license_verified,
                })
                print(f"  [ADDED] Concept {concept_id} ({concept_title}) -> {title} ({channel})")
            except Exception as e:
                missing_concepts.append(f"Concept {concept_id}: {concept_title} - DB Insert failed: {e}")
        else:
            if not any(concept_title in m for m in missing_concepts):
                missing_concepts.append(f"Concept {concept_id}: {concept_title} - No confident educational video found")
            rejected_videos.extend(all_rejected[:5])  # Keep top 5 rejections per concept

        # Small delay between concepts
        time.sleep(0.3)

    # Write report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("VIDEO POPULATION REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.datetime.utcnow().isoformat()}\n\n")
        f.write(f"Total concepts: {len(concepts)}\n")
        f.write(f"Already had videos (skipped): {skipped_existing}\n")
        f.write(f"Videos successfully added: {len(added_videos)}\n")
        f.write(f"Concepts still missing videos: {len(missing_concepts)}\n\n")

        f.write("--- ADDED VIDEOS ---\n")
        for v in added_videos:
            f.write(f"  Concept {v['concept_id']} ({v['concept_title']})\n")
            f.write(f"    Video: {v['video_title']}\n")
            f.write(f"    Channel: {v['channel']}\n")
            f.write(f"    URL: {v['url']}\n")
            f.write(f"    License: {v['license']} (verified={v['license_verified']})\n\n")

        f.write("\n--- MISSING CONCEPTS ---\n")
        for m in missing_concepts:
            f.write(f"  {m}\n")

        f.write(f"\n--- REJECTED VIDEOS (Sample) ---\n")
        for r in rejected_videos[:100]:
            f.write(f"  {r}\n")

    conn.close()
    print(f"\nPopulation complete. Report: {REPORT_PATH}")
    print(f"Added: {len(added_videos)}, Skipped existing: {skipped_existing}, Missing: {len(missing_concepts)}")


if __name__ == "__main__":
    populate_videos()
