# Technical Specification — AURA Architecture

## 1. Technology Stack
* **API Gateway:** FastAPI (Asynchronous Python 3.11+)
* **Relational Storage:** SQLite with SQLAlchemy 2.0 ORM (`aura.db`)
* **Authentication:** PyJWT (HS256 signature), PBKDF2 HMAC-SHA256 (100,000 iterations, 16-byte random salt per user)
* **Task Automation:** APScheduler (Background cron daemons for midnight audits)
* **Inference Layer:** Dual-Path Failover Router
  * *Primary Cloud:* Groq API (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`)
  * *Local Fallback:* Ollama (`llama3.2:3b`, `qwen3:4b`, `nomic-embed-text`)
* **Voice Engine:** Local SAPI5 / pyttsx3 voice synthesizer for offline audio briefings
* **Frontend Surface:** Glassmorphic Streamlit Dashboard (Port 8501) / Decoupled 3D WebGL Canvas (Three.js)

## 2. Security & Data Protection Spec
* **Environment Protection:** Secrets (`GROQ_API_KEY`, `SECRET_KEY`) read strictly via `python-dotenv` from `.env`.
* **Exclusion Enforcements:** `.gitignore` locks `.env`, `aura.db`, `artifacts_storage/`, and log dumps out of version control.
* **Per-Tenant Partitioning:** Uploaded user artifacts and profile avatars are isolated into `artifacts_storage/user_<id>/` and `artifacts_storage/avatars/`.
* **Zero Trust Endpoint Resolution:** Endpoints extract user context via `Depends(get_current_user)`; URL spoofing (`?user_id=X`) is rejected.

## 3. Subsystem Breakdown
* `llm_router.py`: Handles transparent failover across cloud and local engines.
* `agent_worker.py`: Autonomous daemon checking streak decays, consuming freeze shields, and activating recovery challenges.
* `vector_service.py`: Computes 768-dimension embeddings via local `nomic-embed-text` with cosine similarity ranking.
* `briefing_service.py`: Compiles pending goals and reminders into a natural-language script for voice delivery.