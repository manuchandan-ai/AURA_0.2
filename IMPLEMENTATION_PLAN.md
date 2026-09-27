# Implementation Plan & Hardening Matrix

| Phase | Milestone | Priority | Verification Criteria |
| :--- | :--- | :--- | :--- |
| **1. Security** | Replace query-param auth with JWT Bearer tokens | P0 | Non-bearer HTTP calls return 401 |
| **2. Storage** | Fix Artifact multipart upload & disk writing | P0 | Files persist in `artifacts_storage/user_<id>/` |
| **3. Vector RAG**| Wire `nomic-embed-text` into `/chat/artifact` | P1 | Chat responses cite exact document chunks |
| **4. Streak Engine**| Autonomous decay and freeze recovery system | P1 | Missed check-in activates shield or challenge |
| **5. Frontend** | Streamlit nav binding and user state greeting | P2 | Single click switches views; greeting displays operator name |