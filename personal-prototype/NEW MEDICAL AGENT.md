# NEW MEDICAL AGENT

**Status:** În construcție
**Locație workspace:** `Desktop/medical-agent/`
**Ultima actualizare:** 2026-03-03

---

## Structura de Directoare

```
medical-agent/
├── SOUL.md              ← Identitatea și principiile agentului
├── MEMORY.md            ← Memorie pe termen lung (profil, biomarkeri, intervenții)
├── AGENTS.md            ← Fișiere, reguli, formate, fluxuri de date
│
└── workspace/
    ├── ANALIZE/
    │   ├── ARHIVA/          ← Raw data: PDF-uri, poze analize
    │   │   └── [TIP]/[AN]/[LUNA]/
    │   └── PROCESATE/       ← Fișiere .md structurate per set de analize
    │
    ├── BIBLIOTECA/
    │   ├── ARTICOLE/
    │   │   ├── ARHIVA/      ← PDF-uri articole
    │   │   └── PROCESATE/   ← .md: link, titlu, autor, data, rezumat, tags, text
    │   ├── CARTI/
    │   │   ├── ARHIVA/      ← PDF-uri cărți (ordonate alfabetic)
    │   │   └── PROCESATE/   ← .md: info carte, autor, rezumat, text
    │   ├── YOUTUBE/
    │   │   └── PROCESATE/
    │   │       └── [CHANNEL]/   ← .md per video: titlu, data, link, rezumat, tags, transcriere
    │   ├── TWITTER/
    │   │   └── PROCESATE/
    │   │       └── [AUTOR]/     ← .md per thread: link, data, content, tags
    │   └── OTHER/
    │       └── PROCESATE/
    │
    ├── SENZORI/
    │   ├── WITHINGS/
    │   │   └── ARHIVA/[AN]/[LUNA]/   ← Update automat: 8am, 12pm, 11pm
    │   ├── ULTRAHUMAN/
    │   │   └── ARHIVA/[AN]/[LUNA]/   ← Update automat: 8am, 12pm, 5pm, 11pm
    │   └── APPLE/
    │       └── ARHIVA/[AN]/[LUNA]/   ← Update manual
    │
    ├── FARMACIE/
    │   ├── INVENTAR/
    │   │   └── inventar.md           ← Stoc curent (brand, ingrediente, gramaj, tip, cantitate)
    │   ├── SHOPPING_LIST/
    │   │   └── shopping_list.md      ← Generat automat când stoc < 10%
    │   └── ARHIVA/                   ← Suplimente inactive / discontinuate
    │
    └── DAILY_LOGS/
        └── [AN]/[LUNA]/              ← Un fișier .md per zi
            └── template_daily_log.md ← Template de bază
```

---

## Fișiere Agent

| Fișier | Scop |
|--------|------|
| `SOUL.md` | Identitate, personalitate, principii, limite |
| `MEMORY.md` | Profil pacient, biomarkeri, suplimente active, patterns senzori, intervenții |
| `AGENTS.md` | Harta fișierelor, reguli memorie, formate standard, tools |

---

## Tools

| Tool | Tip | Utilizare |
|------|-----|-----------|
| [Scrapling](https://github.com/D4Vinci/Scrapling) | Local | Web scraping general |
| Supadata | API | Extragere transcrieri YouTube |
| PubMed | Skill căutare | Articole științifice medicale |

---

## Pași Următori

- [ ] Completează `MEMORY.md` cu profilul de bază (vârstă, înălțime, condiții, alergii)
- [ ] Importă analizele existente în `ANALIZE/ARHIVA/` și procesează-le
- [ ] Populează `FARMACIE/INVENTAR/inventar.md` cu suplimentele curente
- [ ] Configurează automatizările pentru senzori (Withings, Ultrahuman)
- [ ] Testează fluxul complet: analiză nouă → procesare → actualizare MEMORY


##NOTE 
- cron-uri la 08 / 14 / 18 / 23 cu extragere date de la senzorii medicali
- toate datele de la senzori se scriu in bazele de date dar si in dailylogs. se actualizeaza pe masura ce informatii noi apar in decursul acelei zile DAR si daca de ex aduc date din urma (de ex. spun la data x am zburat. sau la data y am facut _____) 
- daily log contine informatii de la senzori, medicatie, analize, stare (agentul poate sa intrebe la intervale prestabilite), continut masa, apa/lichide baute, informatii despre vreme, zboruri, activitati sportive, analize, etc. Aceste logs se pot modifica si inapoi in timp pe masura ce datele devin disponibile (de ex daca adaug o analiza medicala cu 3 ani in urma se va creea un log cu acele date sau se va actualiza unul existent
- 