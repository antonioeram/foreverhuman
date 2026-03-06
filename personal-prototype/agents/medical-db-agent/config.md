# medical-db-agent — Config

**Rol:** Interogează baze de date medicale (PubMed, Examine) pe query-uri configurate. Salvează .md + ingestează în SQLite + LanceDB.

---

## Cron
```
0 5 * * *     # PubMed — zilnic la 05:00
0 5 * * 1     # Examine — săptămânal, luni 05:00
```

---

## Surse

### PubMed (NCBI E-utilities — gratuit)
**Base URL:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
**Auth:** email required (`tool=medical-agent&email=antonio.eram@gmail.com`)

#### Query-uri configurate
> Adaugă / modifică query-uri în lista de mai jos. Folosesc sintaxa PubMed.

```yaml
pubmed_queries:
  - id: longevity
    query: "longevity[MeSH] AND (aging[tiab] OR lifespan[tiab])"
    max_results: 10
    date_filter: last_30_days
  - id: hrv
    query: "heart rate variability[MeSH] AND biofeedback[tiab]"
    max_results: 5
    date_filter: last_30_days
  - id: supplements
    query: "dietary supplements[MeSH] AND randomized controlled trial[pt]"
    max_results: 10
    date_filter: last_30_days
  - id: sleep
    query: "sleep quality[tiab] AND intervention[tiab]"
    max_results: 5
    date_filter: last_30_days
```

### Examine.com
**Tool:** Scrapling (local)
**Pagini urmărite:** fișe suplimente active din inventar

---

## Flux de procesare (PubMed)
1. `esearch.fcgi` → lista de PMID-uri noi pe fiecare query
2. `efetch.fcgi` → abstract + metadata per PMID
3. Deduplicare vs. SQLite (skip dacă PMID există deja)
4. Generează rezumat + tags
5. Salvează .md
6. SQLite INSERT
7. LanceDB UPSERT

---

## Output

### .md output path
```
workspace/BIBLIOTECA/ARTICOLE/PROCESATE/[YYYY-MM-DD]-[slug].md
```

### Format .md generat
```markdown
# [Titlu articol]

- **Link:** https://pubmed.ncbi.nlm.nih.gov/[PMID]/
- **Autor:** [Autori]
- **Data publicare:** [YYYY-MM-DD]
- **Sursa:** PubMed | PMID: [PMID]
- **Journal:** [Journal name]
- **Tags:** #tag1 #tag2

## Rezumat
[Abstract original sau rezumat generat]

## Relevanță pentru Antonio
[Legătură cu profilul / obiectivele din MEMORY.md]
```

---

## SQLite — Tabele scrise
- `articles` (cu `source='pubmed'`)

## LanceDB — Tabel scris
- `medical_literature`
