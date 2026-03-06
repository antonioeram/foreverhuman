# library-agent — Config

**Rol:** Monitorizează folderul de cărți pentru fișiere noi. La PDF nou detectat: extrage text, generează rezumat + protocoale practice, salvează .md + ingestează în SQLite + LanceDB.

---

## Trigger
**File watcher** (nu cron) — monitorizează folderul:
```
workspace/BIBLIOTECA/CARTI/ARHIVA/
```
La detecție fișier `.pdf` nou → rulează pipeline-ul.

Alternativ cron pentru robustețe:
```
0 4 * * *   # zilnic la 04:00 — verifică dacă există PDF-uri neprocesate
```

---

## Flux de procesare
1. Scanează `CARTI/ARHIVA/` pentru PDF-uri fără .md corespondent în `PROCESATE/`
2. Extrage text din PDF (PyMuPDF / pdfplumber)
3. Chunking → generează rezumat complet + concluzii cheie + protocoale practice
4. Salvează .md în `PROCESATE/`
5. SQLite INSERT
6. LanceDB UPSERT (text chunked 512 tokens, overlap 64)

---

## Convenție denumire fișiere
```
CARTI/ARHIVA/   → [Autor] - [Titlu].pdf
CARTI/PROCESATE/ → [Autor] - [Titlu].md
```

---

## Output

### .md output path
```
workspace/BIBLIOTECA/CARTI/PROCESATE/[Autor] - [Titlu].md
```

### Format .md generat
```markdown
# [Titlu carte]

- **Autor:** [Autor]
- **An apariție:** [An]
- **Tags:** #tag1 #tag2
- **Fișier sursă:** `ARHIVA/[Autor] - [Titlu].pdf`

## Despre carte
[2-3 rânduri: subiect, abordare, credibilitate autor]

## Concluzii cheie
- [idee principală 1]
- [idee principală 2]

## Protocoale / Recomandări practice
[Ce se poate implementa direct, extras din carte]

## Text complet
[Textul integral extras din PDF]
```

---

## SQLite — Tabele scrise
- `books`

## LanceDB — Tabel scris
- `medical_literature`
