# STACK — foreverhuman.health

Decizii tehnice cu rationale. Orice schimbare majoră de stack se documentează aici cu motivul.

---

## Backend — FastAPI (Python 3.12)

**De ce:** async nativ, tipizare strictă cu Pydantic, ecosistem AI/ML Python nativ (LangGraph, Mem0, LanceDB toate sunt Python), OpenAPI auto-generat pentru mobile app.

**Alternativă respinsă:** Node.js/Express — ecosistemul AI e mai slab în JS.

---

## Database — PostgreSQL 16

**De ce:** multi-tenant nativ prin scheme, Row-Level Security, JSONB pentru date flexibile (senzori), tranzacții ACID critice pentru date medicale, Alembic pentru migrări.

**Schema per pacient:** `patient_{uuid}` — izolare completă, query-uri simple, backup granular.

**Alternativă respinsă:** SQLite — nu suportă concurență multi-user, nu are RLS.

---

## Vector DB — LanceDB

**De ce:** local, Python-native, zero infra extra, namespace per pacient, performanță bună sub 1M vectori (suficient pentru use case).

**Alternativă respinsă:** Pinecone/Weaviate — cloud, date pacienți ar ieși din VM.

---

## Pipelines / Cron — n8n (self-hosted)

**De ce:** LLM nu are ce căuta în data pipelines (API calls, parse JSON, write DB). n8n e cod determinist, vizual, 500+ integrări, scheduling built-in. Apelează LLM doar când e necesar (ex: summarize article).

**Alternativă respinsă:** OpenClaw/Claude Code pentru pipelines — LLM overkill pentru sarcini deterministe.

---

## Agent Logic — LangGraph + Mem0

**LangGraph:** state machine pentru agent, SqliteSaver/PostgresSaver pentru checkpointing, human-in-the-loop nativ, control granular al fluxului.

**Mem0:** memorie persistentă între sesiuni. 26% mai precis decât OpenAI Memory (benchmark propriu). Rezolvă problema memory loss între sesiuni. Open source, self-hosted, HIPAA-compatible.

**Alternativă respinsă:** OpenClaw — bun pentru raționament conversațional, nu pentru agenți cu state management strict și validare date medicale.

---

## LLM — Claude API (Anthropic)

**De ce:** cel mai bun la raționament complex, instrucțiuni lungi (SOUL.md), urmărire reguli stricte. Folosit DOAR în agent logic (LangGraph nodes), nu în data pipelines.

**Fallback local:** Ollama + llama3/mistral pentru clinici fără acces internet stabil sau cu cerințe de privacy maximă.

---

## Mobile — React Native + Expo

**De ce:** iOS + Android dintr-un codebase, Expo simplifică build/deploy, comunitate mare, TypeScript nativ.

**State management:** Zustand — simplu, performant, fără boilerplate Redux.

**Push notifications:** Expo Notifications → FCM (Android) + APNs (iOS).

**Alternativă respinsă:** Flutter — ecosistem mai mic, Dart în loc de JS/TS.

---

## Auth — JWT + RBAC

**Access token:** 15 min expiry.
**Refresh token:** 30 zile, rotație la fiecare refresh.
**Roluri:** `patient` / `doctor` / `clinic_admin` / `platform_admin`.
**Librărie:** `python-jose` + `passlib[bcrypt]`.

---

## Infra — Docker Compose per clinică

**De ce:** simplu, portabil, rulează pe orice VPS cu Docker. Nu necesită Kubernetes pentru MVP.

**Servicii per clinică:**
```yaml
services:
  api:        FastAPI
  db:         PostgreSQL 16
  lancedb:    LanceDB server
  n8n:        n8n self-hosted
  redis:      Redis (cache + job queue)
  nginx:      Reverse proxy + SSL (Let's Encrypt)
  infra-agent: Monitoring + auto-repair
```

**Update strategie:** Watchtower pentru auto-pull imagini noi. `scripts/update.sh` pentru migrări DB.

---

## Knowledge Base Server — stack separat

```yaml
services:
  kb-api:      FastAPI (read-only)
  kb-db:       PostgreSQL (articole, metadate)
  kb-lancedb:  LanceDB (embeddings literature)
  kb-n8n:      n8n (ingestori: PubMed, YouTube, web, cărți)
  kb-redis:    Redis (job queue pentru ingestie)
  nginx:       Reverse proxy + SSL
```

---

## Open Source — BSL License (Business Source License)

**Perioadă inițială:** proprietar, uz intern.

**La lansare publică:** BSL 1.1
- Codul e vizibil pe GitHub
- Gratuit pentru: uz personal, self-hosted non-comercial
- Comercial: necesită licență
- Devine Apache 2.0 după 4 ani

**Precedente:** n8n, Sentry, HashiCorp, MariaDB — același model.

---

## Embeddings — text-embedding-3-small (OpenAI)

**De ce:** cel mai bun raport cost/performanță pentru text medical în engleză/română. 1536 dimensiuni.

**Alternativă locală:** `sentence-transformers/all-MiniLM-L6-v2` via Ollama — zero cost, ușor mai slab, pentru clinici offline.
