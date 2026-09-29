[ Unauthenticated User ]
                               │
                               ▼
                   ┌─────────────────────────┐
                   │   AURA Access Gateway   │
                   └───────────┬─────────────┘
                               │
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
  [ Tab: Register ]                         [ Tab: Sign In ]
          │                                         │
(Enter Details & Avatar)                            │
          ▼                                         ▼
[ Status: "pending" ]                    [ Cryptographic Verify ]
│                                         │
▼                                         ├────────────────────────┐
[ Await Admin Review ]                               ▼                        ▼
(Invalid Hash)            (Valid Hash)
│                        │
▼                        ▼
[ 401 Unauthorized ]       [ Check Status ]
│
┌────────────────────────────────────────────────────┤
▼                                                    ▼
[ status == "banned" ]                             [ status == "active" ]
│                                                    │
▼                                                    ▼
[ Show Appeal Form Tab ]                              [ Issue JWT Bearer Token ]
│                                                    │
▼                                                    ▼
[ Post /auth/appeal ]                                  [ Full Platform Deck ]
│
┌───────────────────────┬────────────────────────┬────────────┴───────────┐
▼                       ▼                        ▼                        ▼
[ Home Plane ]        [ Reasoning Chat ]       [ Goals & Plan ]       [ Admin Console ]
- Morning Card        - Freeform Query         - AI Routine Gen       - Approve Queue
- Audio Briefing      - Multi-Input Attach     - Streak Shield        - User Ban/Unban
- Domain Buttons      - Grounded Artifact      - Recovery Mode        - Review Appeals