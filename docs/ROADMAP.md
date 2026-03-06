# ROADMAP — foreverhuman.health

Faze de dezvoltare cu timeline realist. Prioritatea e validarea rapidă a conceptului, nu perfectul tehnic.

---

## Faza 0 — Foundation (Săptămânile 1–2)

**Obiectiv:** Mediul de lucru funcțional, schema DB, Docker Compose de bază.

- [ ] `platform/db/schema.sql` — schema PostgreSQL completă (public + patient_{uuid})
- [ ] `infra/docker-compose.clinic.yml` — stack complet clinică (api, db, redis, nginx)
- [ ] `infra/docker-compose.kb.yml` — stack KB server
- [ ] `scripts/setup-clinic.sh` — deployment automat pe VPS nou
- [ ] FastAPI skeleton cu health check + JWT auth
- [ ] Alembic setup + prima migrare
- [ ] CI simplu (GitHub Actions: lint + test)

**Done când:** `docker compose up` pe un VPS gol → api răspunde la `/health`.

---

## Faza 1 — MVP Personal (Săptămânile 3–6)

**Obiectiv:** Un singur pacient, un agent funcțional, date reale ingerate.

### Backend
- [ ] Auth complet: register, login, refresh token, RBAC
- [ ] Patient CRUD: creare profil, schema dedicată PostgreSQL
- [ ] Upload analize: PDF parsing → biomarkeri extrași → SQLite pacient
- [ ] Agent pacient v1: LangGraph + Mem0 + Claude API
  - Node citire MEMORY (PostgreSQL)
  - Node interpretare analize
  - Node răspuns structurat (Format Output din SOUL.md)
- [ ] Session Boot Protocol implementat (sync MEMORY ↔ PostgreSQL)
- [ ] `validated_write()` — citire înapoi după orice scriere
- [ ] Audit log append-only

### Mobile (skeleton)
- [ ] `app.json` + structură navigație de bază
- [ ] Ecran login
- [ ] Ecran home (placeholder)
- [ ] Conexiune la API (axios + JWT interceptor)

**Done când:** Antonio poate uploada o analiză și agentul o interpretează corect cu surse citate.

---

## Faza 2 — Multi-tenant Clinic (Săptămânile 7–10)

**Obiectiv:** Clinic admin poate adăuga doctori și pacienți. Izolare corectă.

- [ ] Clinic admin flow: creare clinică, invitare doctori, adăugare pacienți
- [ ] Doctor agent v1: acces cross-patient în clinică, rapoarte zilnice
- [ ] Doctor directive system: doctor emite protocol → patient agent primește + implementează
- [ ] Patient notificat când doctorul modifică protocolul
- [ ] Rol `clinic_admin` cu dashboard: listă pacienți, statistici de grup
- [ ] Raport automat zilnic per doctor (n8n cron → PostgreSQL → email)
- [ ] RLS (Row-Level Security) validat — doctor nu poate vedea altă clinică

**Done când:** Clinică demo cu 3 doctori + 10 pacienți funcționează izolat.

---

## Faza 3 — Sub-agenți & Senzori (Săptămânile 11–14)

**Obiectiv:** Date automate — senzori, web, literature.

- [ ] `sensor-agent` n8n pipeline:
  - Withings API (greutate, tensiune, somn)
  - Ultrahuman API (HRV, recovery, glicemie)
  - Apple Health (HealthKit export parser)
- [ ] `medical-db-agent`: PubMed E-utilities → LanceDB KB
- [ ] `medical-web-agent`: Scrapling → articole biohacking → LanceDB KB
- [ ] `youtube-agent`: YouTube API + Supadata transcripturi → LanceDB KB
- [ ] Stale threshold automation — valorile expirate marcate automat
- [ ] Canary values — detectare halucinare la boot
- [ ] Alert system: HRV < 20ms, tensiune > 140/90 → push notification

**Done când:** Datele senzorilor apar automat în profilul pacientului fără input manual.

---

## Faza 4 — Knowledge Base (Săptămânile 15–18)

**Obiectiv:** KB central funcțional, sincronizat în clinici.

- [ ] KB server: FastAPI read-only + PostgreSQL + LanceDB
- [ ] Ingestori n8n: PubMed, YouTube, web, cărți (via docling)
- [ ] KB sync pipeline: clinică primește delta updates de la KB central
- [ ] Semantic search: agentul pacient caută în KB local (LanceDB)
- [ ] Opt-in outcome vectors: anonymizare + trimitere la KB central
- [ ] KB admin dashboard: monitorizare ingestori, calitate embeddings

**Done când:** Agentul citează articole din KB când răspunde la întrebări.

---

## Faza 5 — Mobile App Complet (Săptămânile 19–24)

**Obiectiv:** App React Native productibil pe iOS + Android.

- [ ] Design system: culori, tipografie, componente de bază
- [ ] Onboarding flow: creare cont, completare profil, prima analiză
- [ ] Chat cu agentul: UI conversațional, history
- [ ] Dashboard sănătate: biomarkeri, grafice trend, senzori live
- [ ] Upload analize: camera sau fișier → procesare automată
- [ ] Notificări push: Expo Notifications → FCM + APNs
- [ ] Doctor view: listă pacienți, rapoarte, directive
- [ ] Offline support: date cache local (MMKV)
- [ ] TestFlight + Play Store internal testing

**Done când:** App-ul trece review App Store / Play Store.

---

## Faza 6 — Production Hardening (Săptămânile 25–28)

**Obiectiv:** Pregătit pentru clienți plătitori.

- [ ] Backup automat PostgreSQL: pg_dump + S3 (sau local)
- [ ] `scripts/backup.sh` — backup zilnic, retenție 30 zile
- [ ] `infra-agent`: monitoring Docker health, auto-restart servicii căzute
- [ ] Watchtower: auto-pull imagini noi la deploy
- [ ] GDPR: endpoint cascade delete, export date pacient (JSON)
- [ ] Rate limiting pe API (slowapi)
- [ ] Logging centralizat (structurat, nu plain text)
- [ ] Load test: 50 pacienți simultan per clinică
- [ ] Penetration test basic: auth bypass, SQL injection, SSRF
- [ ] Documentație onboarding clinică nouă (< 30 minute setup)

**Done când:** Prima clinică externă plătitoare live.

---

## Faza 7 — Scale & Open Source (Luna 8+)

**Obiectiv:** Creștere și tranziție BSL.

- [ ] Pricing model validat (per clinică / per pacient / hybrid)
- [ ] Self-serve onboarding: clinică nouă fără intervenție manuală
- [ ] Multi-clinică management pentru `platform_admin`
- [ ] Ollama fallback testat în producție (clinici fără internet stabil)
- [ ] BSL license + cod pe GitHub public
- [ ] Documentație tehnică externă (setup, API reference, agent customization)
- [ ] Community: Discord sau forum pentru self-hosters
- [ ] Evaluare Kubernetes dacă > 50 clinici active

---

## Principii de Prioritizare

1. **Validare rapidă** — MVP cu date reale înainte de orice feature nou.
2. **Nu Kubernetes înainte de Product-Market Fit** — Docker Compose până la 50+ clinici.
3. **GDPR by design** — nu de fixat la final, integrat din Faza 0.
4. **Test pe date reale (Antonio)** — fiecare fază testeaza pe cazul real înainte de generalizare.
5. **BSL deschide codul când există revenue** — nu înainte.
