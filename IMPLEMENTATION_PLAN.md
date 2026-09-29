# Implementation & Validation Plan — AURA

| Milestone | Deliverables | Verification Criteria | Status |
| :--- | :--- | :--- | :--- |
| **M1: Core Security** | Per-user PBKDF2 salting, JWT tokens, `.env` | Raw URL ID spoofing returns 401; keys absent from git | Completed |
| **M2: Governance** | User registration flow with Admin review desk | New accounts enter `pending`; login denied until approved | Completed |
| **M3: Suspension & Appeal**| Ban action, conditional appeal tab display | Banned users unlock appeal form; admins review submissions | Completed |
| **M4: Goal Routine Gen** | Detailed routine + task extraction to reminders | Creating goal auto-populates daily schedule & reminders | Completed |
| **M5: Audio Briefing** | SAPI5/pyttsx3 speech synthesizer for morning routine | Clicking briefing generates and plays daily `.wav` audio | Completed |
| **M6: Multi-Input Bar** | Universal prompt bar with file/photo upload | Uploaded files vectorize and feed directly to AI reasoning | Completed |
| **M7: Chat Sessions** | Named chat history with `+ New Chat` reset | Previous conversations archived in recents; loads cleanly | Completed |