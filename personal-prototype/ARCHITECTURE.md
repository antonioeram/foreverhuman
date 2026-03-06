# ARCHITECTURE — Medical Agent System

**Versiune:** 1.0
**Ultima actualizare:** 2026-03-06

---

## Viziune generală

### Ierarhia datelor — principiu fundamental

```
DB (SQLite + LanceDB)  →  GROUND TRUTH. Sursa de adevăr absolută.
.md files              →  BACKUP. Generate din DB. Read-only pentru agent.
MEMORY.md              →  SNAPSHOT. Generat din DB la boot. Nu e sursă, e oglindă.
```

**Direcția datelor e unidirecțională:**
```
Sursă externă → Sub-agent → DB (SQLite + LanceDB) → .md generate
                                      ↑
                              Agentul citește DE AICI
```

Agentul nu citește din .md ca sursă primară. .md există pentru Antonio (lizibilitate) și ca backup
de urgență dacă DB-ul e inaccesibil — caz în care agentul raportează explicit că lucrează din backup.

---

Sistemul funcționează pe două niveluri:

1. **Sub-agenți** — procese specializate cu cron, fiecare responsabil de o sursă de date. Extrag, normalizează, scriu în DB → generează .md din DB.
2. **Main Agent** — citește din DB (SQLite + LanceDB), analizează continuu, răspunde, alertează. Nu scrie direct în .md — generează .md din ceea ce a scris în DB.

```
┌─────────────────────────────────────────────────────────────┐
│                        SURSE DE DATE                        │
│  Withings  Ultrahuman  Apple   YouTube  Twitter  PubMed     │
│  Senzori   Senzori    Health  Transcrieri  Social  DB Med   │
└─────┬──────────┬─────────┬──────────┬───────┬───────┬──────┘
      │          │         │          │       │       │
      ▼          ▼         ▼          ▼       ▼       ▼
┌─────────────────────────────────────────────────────────────┐
│                        SUB-AGENȚI                           │
│  sensor   sensor    sensor   youtube  social  medical-db    │
│  -agent   -agent   -agent   -agent   -agent   -agent        │
│ (withings)(ultraH)(apple)                    medical-web    │
│                                              library-agent  │
└─────────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
    ┌──────────────────┐   ┌──────────────────────┐
    │   .md files      │   │     BAZE DE DATE      │
    │  (workspace/)    │   │  SQLite + LanceDB     │
    └──────────────────┘   └──────────────────────┘
              │                       │
              └───────────┬───────────┘
                          ▼
            ┌─────────────────────────┐
            │       MAIN AGENT        │
            │  Analiză continuă       │
            │  Corelații              │
            │  Rapoarte & Alertă      │
            └─────────────────────────┘
                          │
                          ▼
                       Antonio
```

---

## Main Agent

**Rol:** Interpretare, corelare, alertă, răspuns la întrebări.
**Nu colectează date** — consumă exclusiv ce sub-agenții au procesat.

### Trigger-e de analiză
| Trigger | Acțiune |
|---------|---------|
| Date noi în SQLite / LanceDB | Rulează analiză incrementală pe datele noi |
| Întrebare directă Antonio | Caută în LanceDB + SQLite + MEMORY.md → răspuns |
| Cron zilnic (ora 07:00) | Digest zilnic: somn, HRV, glicemie, suplimente luate |
| Cron săptămânal (luni 08:00) | Raport săptămânal senzori + biomarkeri + bibliotecă |
| Cron lunar (1 ale lunii) | Review protocol: suplimente, obiective, tendințe |
| Red flag detectat | Alert imediat → format din SOUL.md |

### Ce interoghează
- `SQLite` → date structurate, tendințe, corelații numerice
- `LanceDB` → căutare semantică în literatură, log-uri, interpretări
- `MEMORY.md` → profil, obiective, context permanent
- `.md files` → detalii narrative, transcrieri, texte complete

---

## Sub-Agenți

### 1. `sensor-agent` — Senzori biologici
**Fișier config:** `agents/sensor-agent/config.md`

| Sursă | API | Cron | Date extrase |
|-------|-----|------|--------------|
| Withings | Withings Health API | 08:00, 12:00, 23:00 | greutate, compoziție corporală, tensiune, puls, somn |
| Ultrahuman | Ultrahuman API | 08:00, 12:00, 17:00, 23:00 | recovery score, HRV, somn, glicemie, activitate |
| Apple Health | HealthKit export | manual (la sync) | pași, VO2max, calorii, frecvență cardiacă |

**Output .md:** `workspace/SENZORI/[DEVICE]/ARHIVA/[AN]/[LUNA]/[YYYY-MM-DD].md`
**SQLite:** tabelele `sensor_readings`, `sleep_log`, `body_composition`
**LanceDB:** tabelul `daily_observations`

---

### 2. `social-agent` — Rețele sociale
**Fișier config:** `agents/social-agent/config.md`

| Sursă | API | Cron | Date extrase |
|-------|-----|------|--------------|
| Twitter/X | Twitter API v2 | 06:00 zilnic | threaduri de la autori urmăriți (biohacking, longevitate, medicină) |

**Output .md:** `workspace/BIBLIOTECA/TWITTER/PROCESATE/[AUTOR]/[YYYY-MM-DD]-[slug].md`
**SQLite:** tabela `social_content`
**LanceDB:** tabelul `medical_literature`

---

### 3. `youtube-agent` — YouTube
**Fișier config:** `agents/youtube-agent/config.md`

| Sursă | API | Cron | Date extrase |
|-------|-----|------|--------------|
| YouTube | YouTube Data API v3 | 06:00 zilnic | videouri noi de pe canale urmărite |
| Transcriere | Supadata API | la detectare video nou | transcriere completă |

**Output .md:** `workspace/BIBLIOTECA/YOUTUBE/PROCESATE/[CHANNEL]/[YYYY-MM-DD]-[slug].md`
**SQLite:** tabela `youtube_videos`
**LanceDB:** tabelul `youtube_transcripts`

---

### 4. `medical-web-agent` — Site-uri medicale
**Fișier config:** `agents/medical-web-agent/config.md`

| Sursă | Tool | Cron | Date extrase |
|-------|------|------|--------------|
| Site-uri configurate | Scrapling (local) | 05:00 zilnic | articole noi, studii, blog posts medicale |

**Output .md:** `workspace/BIBLIOTECA/OTHER/PROCESATE/[YYYY-MM-DD]-[slug].md`
**SQLite:** tabela `web_articles`
**LanceDB:** tabelul `medical_literature`

---

### 5. `medical-db-agent` — Baze de date medicale
**Fișier config:** `agents/medical-db-agent/config.md`

| Sursă | API | Cron | Date extrase |
|-------|-----|------|--------------|
| PubMed | NCBI E-utilities API | 05:00 zilnic | articole noi pe query-uri configurate |
| Examine.com | Scrapling | săptămânal | actualizări fișe suplimente |

**Output .md:** `workspace/BIBLIOTECA/ARTICOLE/PROCESATE/[YYYY-MM-DD]-[slug].md`
**SQLite:** tabela `pubmed_articles`
**LanceDB:** tabelul `medical_literature`

---

### 6. `library-agent` — Cărți (manual + procesare automată)
**Fișier config:** `agents/library-agent/config.md`

| Input | Cron | Procesare |
|-------|------|-----------|
| PDF adăugat manual în `BIBLIOTECA/CARTI/ARHIVA/` | La detectare fișier nou | Extrage text, rezumă, creează .md |

**Output .md:** `workspace/BIBLIOTECA/CARTI/PROCESATE/[Titlu-Autor].md`
**SQLite:** tabela `books`
**LanceDB:** tabelul `medical_literature`

---

## Baze de Date

### SQLite — `workspace/DATABASE/sqlite/medical.db`
Date structurate, relaționale, interogabile numeric și temporal.

#### Schema

```sql
-- Senzori
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY,
    device TEXT,           -- 'withings' | 'ultrahuman' | 'apple'
    metric TEXT,           -- 'hrv' | 'weight' | 'glucose' | etc.
    value REAL,
    unit TEXT,
    recorded_at TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sleep_log (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE,
    device TEXT,
    duration_min INTEGER,
    deep_sleep_min INTEGER,
    rem_sleep_min INTEGER,
    hrv_avg REAL,
    recovery_score INTEGER,  -- Ultrahuman
    rhr INTEGER,
    notes TEXT
);

CREATE TABLE body_composition (
    id INTEGER PRIMARY KEY,
    date DATE,
    device TEXT,
    weight_kg REAL,
    fat_pct REAL,
    muscle_kg REAL,
    water_pct REAL,
    bmi REAL
);

-- Biomarkeri din analize
CREATE TABLE biomarkers (
    id INTEGER PRIMARY KEY,
    date DATE,
    indicator TEXT,
    value REAL,
    unit TEXT,
    reference_min REAL,
    reference_max REAL,
    lab TEXT,
    source_file TEXT,      -- path la .md sursă
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suplimente
CREATE TABLE supplements (
    id INTEGER PRIMARY KEY,
    name TEXT,
    brand TEXT,
    form TEXT,             -- 'capsule' | 'powder' | 'liquid'
    dose TEXT,
    frequency TEXT,
    reason TEXT,
    start_date DATE,
    end_date DATE,         -- NULL dacă activ
    active INTEGER DEFAULT 1
);

CREATE TABLE supplement_log (
    id INTEGER PRIMARY KEY,
    supplement_id INTEGER REFERENCES supplements(id),
    date DATE,
    dose_taken TEXT,
    time_taken TEXT,
    notes TEXT
);

CREATE TABLE supplement_stock (
    id INTEGER PRIMARY KEY,
    supplement_id INTEGER REFERENCES supplements(id),
    current_units INTEGER,
    max_units INTEGER,
    pct_remaining REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medicamente
CREATE TABLE medications (
    id INTEGER PRIMARY KEY,
    name TEXT,
    dose TEXT,
    frequency TEXT,
    prescribed_by TEXT,
    start_date DATE,
    end_date DATE,
    active INTEGER DEFAULT 1
);

-- Jurnal zilnic
CREATE TABLE daily_logs (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE,
    energy_score INTEGER,  -- 1-10
    notes TEXT,
    source_file TEXT
);

-- Intervenții
CREATE TABLE interventions (
    id INTEGER PRIMARY KEY,
    date DATE,
    type TEXT,             -- 'supliment' | 'dieta' | 'antrenament' | 'medicament'
    description TEXT,
    reason TEXT,
    result TEXT,
    status TEXT            -- 'activ' | 'finalizat' | 'abandonat'
);

-- Bibliotecă
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    source TEXT,           -- 'pubmed' | 'substack' | 'journal' | etc.
    publish_date DATE,
    url TEXT,
    tags TEXT,             -- JSON array
    summary TEXT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    year INTEGER,
    tags TEXT,
    summary TEXT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE youtube_videos (
    id INTEGER PRIMARY KEY,
    channel TEXT,
    title TEXT,
    url TEXT,
    publish_date DATE,
    tags TEXT,
    summary TEXT,
    has_transcript INTEGER DEFAULT 0,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE social_content (
    id INTEGER PRIMARY KEY,
    platform TEXT,         -- 'twitter' | 'substack' etc.
    author TEXT,
    url TEXT,
    date DATE,
    content TEXT,
    tags TEXT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### LanceDB — `workspace/DATABASE/lancedb/`
Date vectoriale pentru căutare semantică. Main Agentul face RAG (Retrieval-Augmented Generation) pe toate sursele.

#### Tabele (collections)

| Tabelă | Conținut | Chunk strategy |
|--------|----------|----------------|
| `medical_literature` | Articole PubMed, cărți, web, Twitter | 512 tokens, overlap 64 |
| `youtube_transcripts` | Transcrieri complete video | 512 tokens, overlap 64 |
| `biomarker_interpretations` | Interpretările narrative din analizele procesate | Per analiză |
| `daily_observations` | Textul narativ din daily logs | Per zi |
| `genetic_insights` | Rezultate genetice procesate | Per variantă / secțiune |

#### Schema per document vectorial
```json
{
  "id": "uuid",
  "content": "textul chunkului",
  "embedding": [/* vector float32 */],
  "source_type": "article | book | youtube | twitter | biomarker | daily_log | genetic",
  "source_file": "path/to/file.md",
  "date": "YYYY-MM-DD",
  "tags": ["tag1", "tag2"],
  "metadata": {}
}
```

---

## Pipeline Date — Flux Complet

```
[Sursă externă: API / PDF / file watcher]
   │
   ▼
[Sub-agent extrage & normalizează]
   │
   ├──► validated_write() → SQLite INSERT
   │         └── read-back verify → audit_log (SQLite)
   │
   ├──► LanceDB UPSERT (embedding text)
   │         └── verify chunk count → audit_log
   │
   └──► generate_md_from_db() → .md file (workspace/)
             └── .md e OUTPUT, nu input
              │
              ▼
        [Session Boot — obligatoriu]
        1. interogare SQLite → valorile curente
        2. regenerează MEMORY.md din SQLite
        3. marchează [STALE] conform thresholds
        4. verifică canary values
        5. raportează boot status
              │
              ▼
        [Main Agent — citește DOAR din DB]
        SQLite → date numerice, tendințe, corelații
        LanceDB → căutare semantică (RAG)
        MEMORY.md → citit NUMAI dacă SQLite inaccesibil
                    → caz în care raportează [FALLBACK:md]
        Orice valoare citată → sursa din DB specificată explicit
              │
              ▼
           Antonio
              │
              ▼ (opțional, la cerere)
        [Export .md / raport]
        Generat din DB, nu din context agent
```

---

## Enforcement Anti-Halucinare

> Vezi `VALIDATION.md` pentru specificații tehnice complete.

**Stratificare pe 7 niveluri:**

| Nivel | Mecanism | Ce prinde |
|-------|----------|-----------|
| 1 | `validated_write()` — read-back după orice scriere | Write eșuat / valoare greșită în DB |
| 2 | Confidence tags `[VERIFIED]` / `[STALE]` / `[CONFLICT]` | Valori fără sursă sau expirate |
| 3 | Session boot protocol — sync MEMORY.md ↔ SQLite | Discrepanțe acumulate între sesiuni |
| 4 | Audit log append-only (`DATABASE/audit.log`) | Orice acțiune falsă ("am scris dar nu e în log") |
| 5 | Git pe workspace/ — commit după fiecare modificare | Modificări neautorizate, rollback la erori |
| 6 | Stale thresholds per indicator | Date vechi prezentate ca actuale |
| 7 | Canary values — valori test cu răspuns cunoscut | Halucinare completă — sesiunea se oprește |

**Regula de aur:** SQLite e ground truth. MEMORY.md e oglindă. Dacă diferă → MEMORY.md e greșit.

**SQLite — tabele suplimentare pentru enforcement:**

```sql
-- Audit trail (append-only)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT,               -- 'write' | 'read' | 'sync' | 'error' | 'boot'
    agent TEXT,                -- 'main' | 'sensor-agent' | etc.
    target TEXT,               -- 'MEMORY.md' | 'SQLite/biomarkers' | etc.
    key TEXT,
    old_value TEXT,
    new_value TEXT,
    source TEXT,
    verified INTEGER,          -- 1 = read-back ok, 0 = failed
    error_msg TEXT
);

-- Confidence state per câmp MEMORY.md
CREATE TABLE memory_confidence (
    id INTEGER PRIMARY KEY,
    field TEXT UNIQUE,
    confidence TEXT,           -- 'VERIFIED' | 'INFERRED' | 'STALE' | 'CONFLICT' | 'UNVERIFIED'
    source TEXT,
    last_verified TIMESTAMP,
    stale_threshold_days INTEGER
);

-- Canary values
CREATE TABLE canary_values (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE,
    expected_value TEXT,
    last_checked TIMESTAMP,
    last_result TEXT           -- 'PASS' | 'FAIL'
);
```

---

## Tehnologii

| Componentă | Tehnologie | Note |
|------------|------------|------|
| Orchestrare cron | `cron` (Linux/Mac) sau `launchd` (Mac) | Un job per sub-agent |
| Storage structurat | SQLite | Fișier local, zero infra |
| Storage vectorial | LanceDB | Local, Python SDK |
| Embeddings | `text-embedding-3-small` (OpenAI) sau model local | Per chunk .md |
| Web scraping | Scrapling (local) | `github.com/D4Vinci/Scrapling` |
| YouTube transcripts | Supadata API | |
| Withings API | OAuth 2.0 | Credentials în `.env` |
| Ultrahuman API | API Key | Credentials în `.env` |
| Twitter API | Bearer Token v2 | Credentials în `.env` |
| YouTube API | Google API Key | Credentials în `.env` |
| PubMed API | NCBI E-utilities (gratuit) | Email required |
| Runtime sub-agenți | Python 3.11+ | requirements per agent |
