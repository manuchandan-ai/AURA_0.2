import sqlite3
import os

DB_PATH = "D:/aura/aura.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database will be auto-created on boot.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    def add_col(tbl, col_def):
        cur.execute(f"PRAGMA table_info({tbl})")
        cols = [r[1] for r in cur.fetchall()]
        name = col_def.split()[0]
        if name not in cols:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col_def}")
            print(f"Added {name} to {tbl}")

    add_col("goals", "daily_routine TEXT")
    add_col("reminders", "source TEXT DEFAULT 'Manual'")

    # Create new tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT DEFAULT 'New Conversation',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversation_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS goal_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER,
        task_description TEXT NOT NULL,
        scheduled_time TEXT DEFAULT 'Daily',
        is_completed BOOLEAN DEFAULT 0,
        FOREIGN KEY(goal_id) REFERENCES goals(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Migration to v2 schema complete!")

if __name__ == "__main__":
    migrate()