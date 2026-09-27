import sqlite3
import os

DB_PATH = "D:/aura/aura.db"

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Exiting.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Check existing columns in 'users'
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]

    if "status" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
        print("Added column: status")
    else:
        print("Column 'status' already exists.")

    if "ban_reason" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT")
        print("Added column: ban_reason")
    else:
        print("Column 'ban_reason' already exists.")

    # 2. Make sure existing users are set to 'active'
    cur.execute("UPDATE users SET status = 'active' WHERE status IS NULL OR username = 'admin'")

    # 3. Create 'appeal_requests' table if missing
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appeal_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        appeal_type TEXT DEFAULT 'unban',
        message TEXT NOT NULL,
        admin_response TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    print("Verified 'appeal_requests' table.")

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    run_migration()