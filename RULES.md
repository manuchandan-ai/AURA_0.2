# Engineering & Architecture Rules — AURA

1. **Zero Credential Exposure:** Under no circumstances are `.env` files, API keys, or raw SQLite database binaries to be checked into version control.
2. **Universal Audience Neutrality:** UI copy, modules, and system prompts must remain inclusive of all everyday users (academics, health, career, creators, engineers).
3. **No Unauthenticated Identity Trust:** Never accept or trust `user_id` or `admin_id` passed via URL query parameters or request bodies. Identity must resolve strictly through `Depends(get_current_user)` via signed JWT Bearer tokens.
4. **Resilient Inferencing Guarantee:** Every LLM call must route through `run_llm_with_failover`. A failure on Groq Cloud must automatically fall back to local Ollama with zero server crashes.
5. **Non-Destructive Schema Evolution:** Any schema addition must be executed via backward-compatible migration scripts without dropping existing user goals or conversation logs.
6. **Graceful Momentum Maintenance:** Streaks must never be wiped instantaneously on a single missed day; the platform must prioritize Freeze Shield deduction or Recovery Challenge activation.