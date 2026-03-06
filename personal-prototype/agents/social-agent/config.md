# social-agent — Config

**Rol:** Monitorizează autori pe Twitter/X. La tweet / thread nou relevant: extrage, procesează, salvează .md + ingestează în SQLite + LanceDB.

---

## Cron
```
0 6 * * *   # zilnic la 06:00
```

---

## Credentials (`.env`)
```
TWITTER_BEARER_TOKEN=
```

---

## Autori Urmăriți
> Adaugă / elimină autori. Specifică focus pentru context Main Agent.

```yaml
twitter_accounts:
  - handle: "PeterAttiaMD"
    focus: "longevitate, medicina functionala, performanta"
  - handle: "hubermanlab"
    focus: "neurologie, somn, focus, dopamina"
  - handle: "foundmyfitness"
    focus: "longevitate, genetica, nutrientie"
  - handle: "bryan_johnson"
    focus: "biohacking, anti-aging, protocol"
  # Adaugă mai jos
```

---

## Filtru conținut
Procesează doar tweet-urile / thread-urile care conțin cel puțin un keyword din:
```yaml
keywords:
  - longevity | longevitate
  - biohacking
  - HRV | heart rate variability
  - sleep | somn
  - supplement | supliment
  - glucose | glicemie
  - VO2max
  - inflammation | inflamatie
  - protocol
  - study | studiu | research
```

---

## Flux de procesare
1. Twitter API v2 → timeline per user (din ultima rulare)
2. Filtru keyword
3. Deduplicare vs. SQLite
4. Agregare thread (tweet-urile unui thread se combină)
5. Generează tags
6. Salvează .md
7. SQLite INSERT
8. LanceDB UPSERT

---

## Output

### .md output path
```
workspace/BIBLIOTECA/TWITTER/PROCESATE/[AUTOR]/[YYYY-MM-DD]-[slug].md
```

### Format .md generat
```markdown
# [Subiect thread / primele cuvinte] — @[autor]

- **Link:** [URL primul tweet]
- **Data:** [YYYY-MM-DD]
- **Tags:** #tag1 #tag2

## Content
[Textul complet al threadului, tweet cu tweet]
```

---

## SQLite — Tabele scrise
- `social_content`

## LanceDB — Tabel scris
- `medical_literature`
