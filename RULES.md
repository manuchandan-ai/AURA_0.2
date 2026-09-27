# Engineering & Architecture Rules — AURA

1. **Zero Credential Exposure:** Never commit `.env`, `aura.db`, or plain-text API keys to source control.
2. **Strict Identity Isolation:** No endpoint may accept an arbitrary `user_id` in request bodies or query parameters. Identity must resolve via `Depends(get_current_user)`.
3. **Resilient Inferencing:** All AI completions must route through `run_llm_with_failover`. A failure on Groq Cloud must never result in an unhandled 500 error.
4. **Physical File Containment:** Artifacts must always be partitioned by tenant (`artifacts_storage/user_<id>/`).
5. **State Predictability:** Frontend UI views must derive identity and role privileges strictly from the verified session token.