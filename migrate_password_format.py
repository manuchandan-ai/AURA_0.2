"""
One-time migration: run this ONCE after pulling the new auth.py.

The old auth.py used a single hardcoded salt shared by every user's password.
The new auth.py generates a random salt per user and stores it as
'salt_hex:key_hex' in the same password_hash column, so old hashes no longer
verify. This script re-hashes every existing user's password using their
CURRENT known password where possible, or resets known default accounts.

For the two seeded demo accounts (admin/admin123, john/operator123) this is
fully automatic. If you registered other real accounts with real passwords,
add them to the KNOWN_PASSWORDS dict below before running, or they'll need
to reset their password after this runs (any login will fail harmlessly,
you can then create a fresh account for them).

Usage:
    python migrate_password_format.py
"""
from database import SessionLocal, User
from auth import hash_password

KNOWN_PASSWORDS = {
    "admin": "admin123",
    "john": "operator123",
    # "someusername": "their_real_password",
}


def migrate():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        updated = 0
        skipped = []
        for u in users:
            if u.username in KNOWN_PASSWORDS:
                u.password_hash = hash_password(KNOWN_PASSWORDS[u.username])
                updated += 1
            else:
                skipped.append(u.username)
        db.commit()
        print(f"Re-hashed {updated} user(s) with the new per-user-salt format.")
        if skipped:
            print(f"Skipped (unknown password, will need a manual reset): {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
