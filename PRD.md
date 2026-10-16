# Product Requirements Document (PRD) — AURA
**Product Name:** AURA (Adaptive Unified Reasoning Assistant)  
**Version:** 2.0 (Hardened Governance & Universal Access)  
**Status:** In Production  
**Target Audience:** Universal — Students, professionals, fitness enthusiasts, founders, creators, and general operators.

---

## 1. Problem Statement
Everyday individuals and knowledge workers struggle with fragmented digital workflows across disconnected AI chats, static habit checklists, and scattered personal notes. Context is erased after every conversation, habits collapse due to rigid streak punishment, and external cloud AI tools suffer from rate limits and vendor lock-in. Furthermore, shared productivity apps lack enterprise-grade user lifecycle governance and tamper-resistant authentication.

## 2. Core Value Propositions
* **Universal Domain Intelligence:** Multi-faceted assistance spanning Academic Learning, Fitness & Health, Career Growth, Personal Finance, and Software Engineering.
* **Cognitive Continuity & Memory:** Background cognitive extraction retains user preferences, personal constraints, and ongoing routines across sessions.
* **Resilient Momentum Engine:** Strategic roadmaps with automated daily routines, Streak Freeze shields, and a 24-hour Recovery Protocol to prevent abandonment.
* **Multi-Input Grounded Reasoning:** Ingest documents, study notes, images, and spreadsheets for localized vector retrieval (RAG) using local embeddings.
* **Enterprise Security & Governance:** Cryptographic PBKDF2 per-user salted authentication, signed JWT Bearer access control, and complete administrator lifecycle moderation (Approvals, Suspensions, Appeals).

## 3. User Personas
<<<<<<< HEAD
1. **The Academic / Student:** Breaks down complex subjects via the Feynman technique, parses lecture slides, and tracks study milestones.
2. **The Health & Fitness Operator:** Designs workout splits, maintains training streaks with freeze shield protection, and receives morning voice briefings.
3. **The Professional & Freelancer:** Ingests contracts, drafts salary negotiation scripts, and tracks multi-phase client deliverables.
4. **The System Administrator:** Audits operator activity, approves new registrations, mitigates suspicious access, and reviews ban appeals.
=======
AURA is designed as a universal cognitive engine for **all types of users**. While historically optimized for specific niches, the architecture now seamlessly adapts to any workflow. Key examples include, but are not limited to:
1. **The Academic / Student:** Breaks down complex subjects via the Feynman technique, parses lecture slides, and tracks study milestones.
2. **The Health & Fitness Operator:** Designs workout splits, maintains training streaks with freeze shield protection, and receives morning voice briefings.
3. **The Professional, Creator & Founder:** Ingests contracts, drafts negotiation scripts, brainstorms content, and tracks multi-phase project deliverables.
4. **The General Operator:** Organizes daily life routines, recipes, travel, and personal finance without friction.
5. **The System Administrator:** Audits operator activity, approves new registrations, mitigates suspicious access, and reviews ban appeals.
>>>>>>> 3cf5d74 (chore: update documentation, backend logic, and frontend configuration files)

## 4. Key Performance Indicators (KPIs)
* **Auth Integrity:** 100% of non-public endpoints guarded by verified JWT Bearer tokens.
* **Failover Uptime:** Zero-latency switch from cloud to local Ollama fallback upon API exhaustion.
* **Retention:** Measurable reduction in user abandonment via Streak Freeze shields and recovery challenges.