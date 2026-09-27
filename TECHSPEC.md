# Technical Specification — AURA

## 1. Architecture Stack
* **Gateway / API:** FastAPI (Async Python 3.11+)
* **Database ORM:** SQLAlchemy 2.0 with SQLite engine (`aura.db`)
* **Task Scheduling:** APScheduler (Background cron)
* **Intelligence Layer:** Groq API (`openai/gpt-oss-120b`), Ollama (`llama3.2:3b`, `nomic-embed-text`)
* **Frontend Surface:** Streamlit (Cyberpunk glassmorphic design) / Extensible Web UI
* **Security & Auth:** PyJWT (HS256), PBKDF2 HMAC-SHA256 with per-user salt

## 2. Subsystems
* `llm_router.py`: Dual-path failover client handling cloud timeout and fallback.
* `vector_service.py`: Document chunking (600 characters, 100-character overlap) and cosine similarity matching.
* `agent_worker.py`: Autonomous midnight decay job managing streak reductions and shield consumption.