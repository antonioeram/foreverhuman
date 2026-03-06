# youtube-agent — Config

**Rol:** Monitorizează canale YouTube configurate. La video nou: descarcă metadata + transcriere via Supadata. Salvează .md + ingestează în SQLite + LanceDB.

---

## Cron
```
0 6 * * *   # zilnic la 06:00
```

---

## Credentials (`.env`)
```
YOUTUBE_API_KEY=
SUPADATA_API_KEY=
```

---

## Canale Urmărite
> Adaugă / elimină canale în lista de mai jos.

```yaml
channels:
  - id: ""       # ex: UCxxxxxx
    name: ""     # ex: Peter Attia
    focus: ""    # ex: longevitate, VO2max, hormoni
  - id: ""
    name: ""
    focus: ""
```

---

## Flux de procesare
1. YouTube Data API v3 → listează videouri noi de pe canale (din ultima rulare)
2. Pentru fiecare video nou:
   a. Extrage metadata (titlu, dată, durată, descriere)
   b. Supadata API → transcriere completă
   c. Main Agent (sau model local) → generează rezumat + tags
   d. Salvează .md
   e. SQLite INSERT
   f. LanceDB UPSERT (embedding pe transcriere chunked)

---

## Output

### .md output path
```
workspace/BIBLIOTECA/YOUTUBE/PROCESATE/[CHANNEL]/[YYYY-MM-DD]-[slug].md
```

### Format .md generat
```markdown
# [Titlu video]

- **Canal:** [Nume canal]
- **Link:** [URL]
- **Data publicare:** [YYYY-MM-DD]
- **Durată:** [h:mm:ss]
- **Tags:** #tag1 #tag2

## Rezumat
[Generat automat — 5-10 rânduri]

## Timestamps cheie
- [MM:SS] — [subiect]

## Transcriere
[Text complet]
```

---

## SQLite — Tabele scrise
- `youtube_videos`

## LanceDB — Tabel scris
- `youtube_transcripts` — chunked pe 512 tokens, overlap 64
