# medical-web-agent — Config

**Rol:** Monitorizează site-uri medicale / biohacking configurate. La conținut nou: extrage, procesează, salvează .md + ingestează în SQLite + LanceDB.

---

## Cron
```
0 5 * * *   # zilnic la 05:00
```

---

## Tool
**Scrapling** (local) — `github.com/D4Vinci/Scrapling`

---

## Site-uri Monitorizate
> Adaugă / elimină surse. Specifică selectorul CSS sau XPath pentru conținut articol.

```yaml
sites:
  - name: "Peter Attia Blog"
    url: "https://peterattiamd.com/articles/"
    article_selector: "article"
    type: "blog"
    tags: ["longevitate", "performanta", "medicina"]

  - name: "Andrew Huberman Newsletter"
    url: "https://www.hubermanlab.com/newsletter"
    article_selector: ".newsletter-content"
    type: "newsletter"
    tags: ["neurologie", "somn", "focus"]

  - name: "Rhonda Patrick Blog"
    url: "https://www.foundmyfitness.com/episodes"
    article_selector: ".episode-content"
    type: "podcast-notes"
    tags: ["longevitate", "nutrientie", "genetica"]

  # Adaugă surse noi mai jos
```

---

## Flux de procesare
1. Scrapling → fetch pagina index a fiecărui site
2. Extrage lista de articole noi (titlu + URL)
3. Deduplicare vs. SQLite
4. Pentru fiecare articol nou:
   a. Scrapling → fetch conținut complet
   b. Curăță HTML → text plain
   c. Generează rezumat + tags
   d. Salvează .md
   e. SQLite INSERT
   f. LanceDB UPSERT

---

## Output

### .md output path
```
workspace/BIBLIOTECA/OTHER/PROCESATE/[YYYY-MM-DD]-[slug].md
```

### Format .md generat
```markdown
# [Titlu articol]

- **Link:** [URL]
- **Autor:** [Autor]
- **Data publicare:** [YYYY-MM-DD]
- **Sursa:** [Nume site]
- **Tags:** #tag1 #tag2

## Rezumat
[3-5 rânduri]

## Extras relevant
[Pasaje cheie aplicabile]
```

---

## SQLite — Tabele scrise
- `web_articles` (mapată pe tabela `articles` cu `source='web'`)

## LanceDB — Tabel scris
- `medical_literature`
