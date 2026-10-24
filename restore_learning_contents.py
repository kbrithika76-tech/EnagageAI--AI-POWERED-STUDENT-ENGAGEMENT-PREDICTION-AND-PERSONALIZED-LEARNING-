import sqlite3, os, datetime, sys

# Paths
src = r'd:/dl project/backend/engageai_backup.db_20260908_144923.sqlite'
dst = r'd:/dl project/backend/engageai.db'

if not os.path.exists(src):
    print('Backup source not found:', src)
    sys.exit(1)
if not os.path.exists(dst):
    print('Destination DB not found:', dst)
    sys.exit(1)

src_conn = sqlite3.connect(src)
src_conn.row_factory = sqlite3.Row
src_cur = src_conn.cursor()

dst_conn = sqlite3.connect(dst)
# Preserve existing schema (including license_verified)
# Ensure destination has the column (should already exist)

dst_cur = dst_conn.cursor()

# Fetch all rows from backup learning_contents
src_cur.execute('SELECT * FROM learning_contents')
rows = src_cur.fetchall()
if not rows:
    print('No rows to restore')
    sys.exit(0)

cols = [desc[0] for desc in src_cur.description]
placeholders = ','.join(['?'] * len(cols))
insert_sql = f"INSERT INTO learning_contents ({','.join(cols)}) VALUES ({placeholders})"

# Insert rows, ignoring duplicates (if any) using OR REPLACE to be safe
for row in rows:
    dst_cur.execute(insert_sql, tuple(row))

dst_conn.commit()
print('Restored', len(rows), 'learning_contents rows from backup')

src_conn.close()
dst_conn.close()
