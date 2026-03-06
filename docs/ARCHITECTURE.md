# ARCHITECTURE — foreverhuman.health

**Versiune:** 0.1 (Faza 0)
**Ultima actualizare:** 2026-03-06

---

## Viziune

Platformă multi-tenant de biohacking/wellness în care fiecare pacient are un agent AI personal, izolat complet de ceilalți pacienți. Doctorii au agenți proprii cu acces cross-pacient în cadrul clinicii lor. O bază de date de cunoștințe medicale centrală, fără date personale, servește toate clinicile.

---

## Diagrama sistemului

```
┌─────────────────────────────────────────────────────────────────────┐
│              KNOWLEDGE BASE SERVER (central, foreverhuman.health)   │
│                                                                     │
│  Ingestori: PubMed · YouTube · Cărți · Web · Twitter                │
│  Storage: PostgreSQL (articole) + LanceDB (embeddings)              │
│  Biohacking-only. ZERO date pacienți.                               │
│  Vectori outcome anonimizați (opt-in per pacient).                  │
│  API: read-only, autentificat prin API key per clinică.             │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTPS read-only
        ┌─────────────────┴──────────────────┐
        ▼                                    ▼
┌──────────────────────┐          ┌──────────────────────┐
│   CLINIC VM #1       │          │   CLINIC VM #2       │  ...
│   foreverhuman/prv   │          │   altă clinică       │
│                      │          │                      │
│  ┌────────────────┐  │          │  Docker Compose      │
│  │ FastAPI (api)  │  │          │  identic             │
│  ├────────────────┤  │          │                      │
│  │ PostgreSQL     │  │          └──────────────────────┘
│  │ (schema/pat.)  │  │
│  ├────────────────┤  │
│  │ LanceDB        │  │
│  │ (ns/patient)   │  │
│  ├────────────────┤  │
│  │ n8n pipelines  │  │
│  ├────────────────┤  │
│  │ LangGraph+Mem0 │  │
│  ├────────────────┤  │
│  │ Redis (cache)  │  │
│  └────────────────┘  │
└──────────┬───────────┘
           │ HTTPS + JWT
           ▼
┌──────────────────────┐
│   MOBILE APP         │
│   React Native/Expo  │
│   iOS + Android      │
│                      │
│  Patient interface   │
│  Doctor interface    │
└──────────────────────┘
```

---

## Izolarea datelor (multi-tenant)

### PostgreSQL — scheme per pacient
```
clinic_db/
├── public.*              ← tabele sistem (clinici, doctori, roluri)
├── patient_{uuid}.*      ← toate datele unui pacient
│   ├── biomarkers
│   ├── sensor_readings
│   ├── supplements
│   ├── daily_logs
│   └── audit_log
└── doctor_{uuid}.*       ← workspace doctor (rapoarte, directive)
```

### LanceDB — namespace per pacient
```
lancedb/
├── patient_{uuid}/
│   ├── biomarker_interpretations
│   ├── daily_observations
│   └── genetic_insights
└── shared/
    └── (nimic — shared KB e pe serverul central)
```

---

## Roluri & Permisiuni

| Rol | Acces |
|-----|-------|
| `patient` | Propriile date. Chat cu agentul propriu. |
| `doctor` | Toate datele pacienților din clinica sa. Poate emite directive. Primește rapoarte. |
| `clinic_admin` | Gestionează pacienți, doctori, setări clinică. |
| `platform_admin` | Acces la toate clinicile. Gestionează KB central. |

---

## Fluxul doctorului

```
Doctor vede dashboard cu toți pacienții clinicii
         │
         ├── Vede date în timp real (senzori, biomarkeri, logs)
         │
         ├── Chatează cu agentul unui pacient:
         │   "Explică-mi de ce ai recomandat X lui patient_Y"
         │
         ├── Emite o directivă:
         │   { type: "protocol_change", patient_id: ...,
         │     instruction: "Adaugă Magneziu 400mg seara",
         │     reason: "HRV scăzut 3 zile consecutive" }
         │         │
         │         ▼
         │   Pacientul primește notificare:
         │   "Dr. [Nume] a modificat protocolul tău. [detalii]"
         │         │
         │         ▼
         │   Agentul pacientului implementează directiva
         │
         └── Setează alerte proprii:
             "Notifică-mă dacă CRP > 3 la orice pacient"
```

---

## Agentul pacientului — arhitectură internă

```
[Input: mesaj / date noi / cron trigger]
         │
         ▼
[Session Boot — obligatoriu]
  1. Citește profil din PostgreSQL
  2. Verifică date noi din senzori (n8n → PostgreSQL)
  3. Sincronizează Mem0 (context sesiune anterioară)
  4. Marchează valori [STALE] conform thresholds
         │
         ▼
[LangGraph Agent]
  Node 1: Intent classification
  Node 2: Data retrieval (PostgreSQL + LanceDB)
  Node 3: KB query (KB central read-only)
  Node 4: Reasoning + validation
  Node 5: Response generation
  Node 6: Write results → PostgreSQL (validated_write)
         │
         ▼
[Output: răspuns + acțiuni + audit log]
```

---

## Agentul doctorului — arhitectură internă

```
[Trigger: cron raport / alertă / întrebare doctor]
         │
         ▼
[Acces cross-pacient în clinică]
  - Citește din toate schemele patient_{uuid}
  - Agregare și comparare cross-pacient
  - Identificare patterns la nivel de grup
         │
         ▼
[LangGraph Doctor Agent]
  - Raport zilnic per pacient
  - Raport săptămânal grup
  - Alert management
  - Directive management
         │
         ▼
[Output: dashboard doctor / notificări / rapoarte PDF]
```

---

## Anti-halucinare & Integritate date

Identic cu `medical-agent/VALIDATION.md` — adaptat pentru multi-tenant:

- `validated_write()` pentru orice scriere în PostgreSQL sau LanceDB
- Session boot protocol per pacient
- Audit log append-only în `patient_{uuid}.audit_log`
- Confidence tags pe valorile din profil
- Stale thresholds per tip de dată
- Canary values per pacient (verificate la boot)
- PostgreSQL = ground truth absolut, Mem0 = context sesiune

---

## GDPR Compliance

- Date pacient **nu părăsesc niciodată VM-ul clinicii**
- KB central **nu conține date personale** — doar literatură + vectori outcome anonimizați
- Vectori outcome = opt-in explicit la onboarding
- Doctor acces = implicit prin apartenența la clinică (Model B)
- Pacientul poate exporta toate datele sale (`/api/patient/export`)
- Pacientul poate cere ștergerea (`/api/patient/delete`) — cascade delete pe toate schemele
- Audit log păstrat 5 ani (cerință GDPR pentru date medicale)
- Detalii complete: `docs/GDPR.md`
