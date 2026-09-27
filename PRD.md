# Product Requirements Document (PRD) — AURA
**Product Name:** AURA (Adaptive Unified Reasoning Assistant)  
**Status:** In Production  
**Target Users:** Software engineers, technical founders, and operators.

## 1. Problem Statement
Knowledge workers manage fractured workflows across LLM chat windows, static task lists, and code documents. Context is continuously lost between conversations, goal check-ins decay, and external LLMs suffer from API rate limits.

## 2. Core Value Propositions
* **Context Continuity:** Background cognitive extractors retain constraints and preferences across sessions.
* **Resilient Reasoning:** Primary cloud execution via Groq (`gpt-oss-120b`) with zero-downtime failover to local Ollama (`llama3.2`).
* **Momentum Defense:** Strategic roadmaps with automated Streak Freeze shields and recovery challenges.
* **Grounded Ingestion:** Vector RAG search across user artifacts using local `nomic-embed-text`.

## 3. Success Metrics
* Authentication token verification on 100% of non-public endpoints.
* Zero-latency failover execution during external cloud API downtime.
* Data isolation across multi-tenant operator accounts.