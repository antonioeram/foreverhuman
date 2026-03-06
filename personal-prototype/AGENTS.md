# AGENTS.md — Medical Expert Agent

> Vezi `ARCHITECTURE.md` pentru diagrama completă a sistemului și schema SQLite/LanceDB.

---

## Harta Fișierelor

| Fișier / Folder | Conținut | Update |
|-----------------|----------|--------|
| `SOUL.md` | Identitate, mod de lucru, principii, format output, limite | Rar (manual) |
| `MEMORY.md` | Profil, biomarkeri, suplimente, genetică, patterns, intervenții | La fiecare date noi |
| `ARCHITECTURE.md` | Design sistem complet, schema DB, flux date | La modificări arhitecturale |
| `agents/sensor-agent/config.md` | Config Withings, Ultrahuman, Apple | La modificare API / cron |
| `agents/youtube-agent/config.md` | Config canale + Supadata | La adăugare canale |
| `agents/social-agent/config.md` | Config autori Twitter/X | La adăugare autori |
| `agents/medical-web-agent/config.md` | Config site-uri monitorizate | La adăugare surse |
| `agents/medical-db-agent/config.md` | Config query-uri PubMed + Examine | La ajustare query-uri |
| `agents/library-agent/config.md` | Config procesare cărți PDF | Rar |
| `workspace/ANALIZE/` | Analize laborator (raw + procesate) | La upload manual |
| `workspace/BIBLIOTECA/` | Articole, cărți, YouTube, Twitter | Via sub-agenți |
| `workspace/SENZORI/` | Date Withings, Ultrahuman, Apple | Via sensor-agent |
| `workspace/FARMACIE/` | Inventar + shopping list suplimente | Manual + auto |
| `workspace/DAILY_LOGS/` | Jurnal zilnic | Zilnic |
| `workspace/DATABASE/sqlite/medical.db` | Date structurate relaționale | Continuu (sub-agenți) |
| `workspace/DATABASE/lancedb/` | Embeddings pentru RAG | Continuu (sub-agenți) |

---

## Sub-Agenți — Rezumat

| Agent | Surse | Cron | Output .md | SQLite | LanceDB |
|-------|-------|------|------------|--------|---------|
| `sensor-agent` | Withings, Ultrahuman, Apple | 08:00, 12:00, 17:00, 23:00 | `SENZORI/` | sensor_readings, sleep_log, body_composition | daily_observations |
| `youtube-agent` | YouTube API + Supadata | 06:00 zilnic | `BIBLIOTECA/YOUTUBE/` | youtube_videos | youtube_transcripts |
| `social-agent` | Twitter/X API | 06:00 zilnic | `BIBLIOTECA/TWITTER/` | social_content | medical_literature |
| `medical-web-agent` | Site-uri configurate (Scrapling) | 05:00 zilnic | `BIBLIOTECA/OTHER/` | articles | medical_literature |
| `medical-db-agent` | PubMed API, Examine | 05:00 zilnic / săptămânal | `BIBLIOTECA/ARTICOLE/` | articles | medical_literature |
| `library-agent` | PDF-uri noi în `CARTI/ARHIVA/` | file watcher + 04:00 | `BIBLIOTECA/CARTI/` | books | medical_literature |

---

## Reguli de Memorie (Main Agent)
- **Analize noi** → procesează în format standard → actualizează `MEMORY.md > Biomarkeri`
- **Schimbare supliment** → actualizează `FARMACIE/INVENTAR/inventar.md` + `MEMORY.md > Suplimente`
- **Intervenție nouă** → adaugă în `MEMORY.md > Intervenții & Rezultate`
- **Red flag detectat** → adaugă în `MEMORY.md > Red Flags` + format alert din SOUL.md
- **Review săptămânal senzori** → actualizează `MEMORY.md > Patterns Senzori`
- **Stoc supliment < 10%** → adaugă în `FARMACIE/SHOPPING_LIST/`

### Reguli de integritate (obligatorii)
> Vezi detalii complete în `SOUL.md > Integritate Memorie & Anti-Halucinare`

- **Scriere → verificare obligatorie.** Orice write în MEMORY.md / SQLite / LanceDB se urmează de un read-back pentru confirmare.
- **Nicio valoare fără sursă.** Format: `[valoare] — sursa: [fișier/tabelă/timestamp]`
- **La sesiune nouă → citește MEMORY.md înainte de orice răspuns.** Nu te baza pe starea din sesiunea anterioară.
- **Conflict între surse → raportează, nu decide singur.** Format: `⚠️ Conflict: [sursă A]=X vs [sursă B]=Y`
- **Date lipsă sau vechi → spune explicit.** Nu estima, nu interpola fără să marchezi că faci asta.

---

## Review Schedule (Main Agent)

| Frecvență | Trigger | Acțiune |
|-----------|---------|---------|
| Zilnic — 07:00 | Cron | Digest: somn, HRV, glicemie, suplimente luate |
| Săptămânal — luni 08:00 | Cron | Raport senzori + bibliotecă nouă + tendințe |
| La analize noi | Event | Procesare + actualizare MEMORY + raport comparativ |
| Lunar — 1 ale lunii | Cron | Review protocol suplimente + obiective |
| Trimestrial | Manual | Analize sânge complete + ajustare protocol |
| Red flag | Event (imediat) | Alert format → SOUL.md |

---

## Formate Standard

### Analiză Laborator Procesată (.md)
```markdown
# [Tip Analiză] — [YYYY-MM-DD]

- **Laborator / Sursă:**
- **Medic ordonator:**

## Biomarkeri
| Indicator | Valoare | Referință | vs. anterior | Status |
|-----------|---------|-----------|--------------|--------|
| ...       | ...     | ...       | ↑ ↓ →        | ✅/⚠️/🔴 |

## Interpretare
## Corelații (senzori, suplimente, comportament)
## ⚠️ Puncte de atenție
## Acțiuni recomandate
## Next review: [data]
```

### Daily Log (.md) — `YYYY-MM-DD.md`
```markdown
# Daily Log — YYYY-MM-DD

## Somn
- Durată: h min | Recovery: /100 | HRV: ms | RHR: bpm

## Activitate
- Pași: | Antrenament: | Zone 2: min

## Alimentație
- Calorii: | Proteine: g | Post: h

## Suplimente luate azi
- [ ] [Supliment] — [doza] — [ora]

## Simptome / Observații
## Energie: /10
## Note
```

### Articol Procesat (.md)
```markdown
# [Titlu]
- **Link:** | **Autor:** | **Data:** | **Sursa:** | **Tags:**
## Rezumat
## Extras relevant
```

### Carte Procesată (.md)
```markdown
# [Titlu] — [Autor]
- **An:** | **Tags:**
## Despre carte
## Concluzii cheie
## Protocoale / Recomandări practice
## Text complet
```

### Video YouTube Procesat (.md)
```markdown
# [Titlu] — [Canal]
- **Link:** | **Data:** | **Durată:** | **Tags:**
## Rezumat
## Timestamps cheie
## Transcriere
```

### Thread Twitter/X Procesat (.md)
```markdown
# [Subiect] — @[autor]
- **Link:** | **Data:** | **Tags:**
## Content
```

### Sensor Report Săptămânal (.md)
```markdown
# Sensor Review — Săptămâna [YYYY-WW]
## Withings | ## Ultrahuman | ## Apple Health
## Corelații identificate
## Ajustări necesare
```

---

## Tools Disponibile

| Tool | Tip | Utilizare |
|------|-----|-----------|
| [Scrapling](https://github.com/D4Vinci/Scrapling) | Local Python | Web scraping articole, site-uri |
| Supadata | API | Transcrieri YouTube |
| PubMed E-utilities | API (gratuit) | Căutare articole medicale |
| SQLite | Local DB | Date structurate, interogări temporale |
| LanceDB | Local vector DB | RAG pe toată literatura + log-uri |
