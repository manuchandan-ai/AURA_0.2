# Database Schema Specification — AURA (SQLite)

### Table: `users`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user identifier |
| `username` | VARCHAR(50) | UNIQUE, INDEXED, NOT NULL | Account login username |
| `email` | VARCHAR(120) | NULLABLE | User contact email |
| `phone` | VARCHAR(25) | NULLABLE | Contact telephone |
| `address` | VARCHAR(255) | NULLABLE | Physical location / address |
| `bio` | TEXT | NULLABLE | User focus, studies, or specialty |
| `profile_pic`| VARCHAR(255) | NULLABLE | Local file path to avatar image |
| `password_hash`| VARCHAR(256)| NOT NULL | PBKDF2 HMAC-SHA256 hash |
| `salt` | VARCHAR(64) | NOT NULL | 16-byte random hex salt per user |
| `role` | VARCHAR(20) | DEFAULT 'operator' | 'admin' or 'operator' |
| `status` | VARCHAR(20) | DEFAULT 'pending' | 'pending', 'active', 'banned', 'rejected' |
| `ban_reason` | TEXT | NULLABLE | Administrative justification for ban |
| `freeze_tokens`| INTEGER | DEFAULT 2 | Available streak shield balance |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Account registration date |

### Table: `goals`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Goal record ID |
| `user_id` | INTEGER (FK `users.id`) | Tenant owner ID |
| `intention` | VARCHAR, NOT NULL | User objective statement |
| `timeline` | VARCHAR | Target duration (e.g., '3 months') |
| `daily_routine`| TEXT | Generated morning/evening routine |
| `streak_count` | INTEGER DEFAULT 0 | Active consecutive streak |
| `saved_streak_count`| INTEGER DEFAULT 0 | Protected streak held during recovery |
| `streak_frozen` | BOOLEAN DEFAULT 0 | Whether a freeze token was used today |
| `in_recovery` | BOOLEAN DEFAULT 0 | Flag indicating 24h recovery active |
| `recovery_task`| TEXT NULLABLE | Mini-assignment to restore broken streak |

### Table: `reminders`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Directive record ID |
| `user_id` | INTEGER (FK `users.id`) | Tenant owner ID |
| `task_text` | VARCHAR, NOT NULL | Actionable item description |
| `priority` | VARCHAR DEFAULT 'Medium'| Priority ('High', 'Medium', 'Low') |
| `due_info` | VARCHAR DEFAULT 'Today' | Due schedule |
| `source` | VARCHAR DEFAULT 'Manual'| Origin: 'Manual' or 'Auto-Goal' |
| `is_completed`| BOOLEAN DEFAULT 0 | Completion status |

### Table: `chat_sessions` & `conversation_messages`
| Table | Key Columns | Purpose |
| :--- | :--- | :--- |
| `chat_sessions` | `id`, `user_id`, `title`, `created_at` | Groups message histories into named sessions |
| `conversation_messages` | `id`, `session_id`, `role`, `content`, `timestamp` | Stores individual conversation turns |

### Table: `appeal_requests`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Appeal identifier |
| `user_id` | INTEGER (FK `users.id`) | Banned user identifier |
| `appeal_type` | VARCHAR DEFAULT 'unban' | 'unban' or 'info' |
| `message` | TEXT, NOT NULL | User statement |
| `admin_response`| TEXT NULLABLE | Administrator resolution comments |
| `status` | VARCHAR DEFAULT 'pending' | 'pending', 'resolved', 'dismissed' |