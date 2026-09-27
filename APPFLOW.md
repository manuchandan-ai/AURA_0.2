# Application Flow Map — AURA

[Unauthenticated User]
│
▼
[/auth/login] ────(Invalid)────► [Display Auth Error]
│ (Valid Credentials)
▼
[Issue JWT Bearer Token]
│
├───────────────────────────────────────────────────────┐
▼                                                       ▼
[Operator Session]                         [Admin Session]
├─► Home Dashboard (Summary, Telemetry)          ├─► Cross-Tenant Management
├─► Assistant Chat (General or Grounded Artifact)├─► Global Health Audit
├─► Goals & Streaks (Check-in, Recovery)         └─► Token Adjustments
├─► Artifact Vault (Upload, Ingest, Chunk)
└─► Memory Vault (Cognitive Context Graph)