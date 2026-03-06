# VALIDATION — Enforcement Anti-Halucinare

> Prompt-urile nu pot enforce nimic. Acest fișier descrie mecanismele tehnice care fac halucinarea
> detectabilă și recuperabilă, indiferent de comportamentul agentului.

---

## Principiu de bază

```
┌─────────────────────────────────────────────────────────┐
│                    GROUND TRUTH                         │
│                                                         │
│   SQLite    ←→   LanceDB                                │
│  (numeric)       (semantic)                             │
│                                                         │
│   Sursa de adevăr. Orice operație pornește de aici.    │
│   Niciodată suprascrise de .md sau de agent direct.    │
└──────────────────────────┬──────────────────────────────┘
                           │ generate din DB
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKUP HUMAN-READABLE                  │
│                                                         │
│   MEMORY.md  /  .md files în workspace/                │
│                                                         │
│   Generate automat din DB. Nu se editează manual        │
│   decât dacă DB-ul e inaccesibil. Orice edit manual    │
│   → sincronizat înapoi în DB imediat.                  │
└─────────────────────────────────────────────────────────┘
                           │ tot ce s-a schimbat
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    AUDIT TRAIL                          │
│                                                         │
│   audit_log (SQLite) + Git history pe workspace/       │
│   Append-only. Niciodată șters.                        │
└─────────────────────────────────────────────────────────┘
```

**Regula ierarhiei — non-negociabilă:**
- DB scrie → .md se regenerează din DB (nu invers)
- .md modificat manual → trebuie sincronizat în DB imediat, altfel e `[UNVERIFIED]`
- Conflict DB vs .md → **DB câștigă întotdeauna**
- Agentul citește din DB, nu din .md (cu excepția boot-ului când DB e inaccesibil)

---

## Nivelul 1 — Validated Write (cod)

**Nicio scriere directă în DB sau fișiere.** Tot merge prin `validated_write()`.

```python
def validated_write(target: str, key: str, value: Any, source: str) -> WriteResult:
    """
    Scrie o valoare și verifică imediat că s-a scris corect.
    Dacă verificarea eșuează → ridică ValidationError, nu continuă.
    """
    # 1. Scrie
    _write(target, key, value)

    # 2. Read-back imediat
    read_back = _read(target, key)

    # 3. Verifică
    if read_back != value:
        raise ValidationError(
            f"Write failed: expected {value}, got {read_back} "
            f"| target={target} | key={key} | source={source}"
        )

    # 4. Loghează în audit trail
    audit_log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "write",
        "target": target,
        "key": key,
        "value": value,
        "source": source,
        "verified": True
    })

    return WriteResult(success=True, value=read_back, source=source)
```

**Ce se întâmplă la eșec:** eroarea e logată în `workspace/DATABASE/audit.log`, operația e oprită,
agentul raportează eșecul explicit — nu continuă ca și cum totul e ok.

---

## Nivelul 2 — Confidence Tags pe valori

Orice valoare din MEMORY.md primește un tag de încredere:

| Tag | Înseamnă |
|-----|----------|
| `[VERIFIED]` | Citit din SQLite / fișier, confirmat prin read-back |
| `[INFERRED]` | Calculat sau estimat — marcat explicit |
| `[STALE:>Nzile]` | Data ultimei verificări depășit pragul |
| `[CONFLICT]` | Două surse dau valori diferite — nerezolvat |
| `[UNVERIFIED]` | Sursă necunoscută sau lipsă |

```markdown
# Exemplu în MEMORY.md
| HRV | 47ms | `[VERIFIED]` — sursa: SQLite/sensor_readings/2026-03-05 |
| Vitamina D | — | `[STALE:>180zile]` — ultima măsurătoare: 2025-08-12 |
| Testosteron | 520 ng/dL | `[CONFLICT]` — Lab A: 520, Lab B: 498, nerezolvat |
```

---

## Nivelul 3 — Session Boot Protocol

La fiecare sesiune nouă, **înainte de orice răspuns**, agentul rulează automat:

```python
def session_boot() -> BootReport:
    """
    Rulează la inițializare. Dacă eșuează → agentul nu pornește.
    """
    report = BootReport()

    # 1. Citește MEMORY.md
    memory = read_file("MEMORY.md")

    # 2. Interoghează SQLite pentru cele mai recente valori
    db_values = sqlite.query("SELECT * FROM biomarkers ORDER BY date DESC LIMIT 50")

    # 3. Compară
    for indicator in db_values:
        memory_val = memory.get(indicator.name)
        if memory_val != indicator.value:
            report.discrepancies.append(Discrepancy(
                field=indicator.name,
                memory_value=memory_val,
                db_value=indicator.value,
                db_date=indicator.date
            ))

    # 4. Dacă există discrepanțe → sincronizează și raportează
    if report.discrepancies:
        sync_memory_from_db(report.discrepancies)
        report.message = f"⚠️ Boot sync: {len(report.discrepancies)} discrepanțe corectate"

    # 5. Verifică timestamp-uri — marchează valorile stale
    mark_stale_values(memory, thresholds=STALE_THRESHOLDS)

    return report
```

**Output la boot:**
```
✅ Session boot: MEMORY.md sincronizat cu SQLite
   - 0 discrepanțe detectate
   - 3 valori marcate [STALE:>90zile]: Vitamina D, Fier, Feritină
   - Ultima actualizare SQLite: 2026-03-05 23:14
```

---

## Nivelul 4 — Audit Trail (append-only)

Fișier: `workspace/DATABASE/audit.log` — **niciodată șters, niciodată modificat.**

```jsonl
{"ts":"2026-03-06T14:32:11Z","action":"write","agent":"main","target":"MEMORY.md","key":"HbA1c","old":"5.6%","new":"5.4%","source":"ANALIZE/PROCESATE/sange-2026-03.md","verified":true}
{"ts":"2026-03-06T14:32:12Z","action":"write","agent":"main","target":"SQLite/biomarkers","key":"HbA1c","old":"5.6","new":"5.4","source":"ANALIZE/PROCESATE/sange-2026-03.md","verified":true}
{"ts":"2026-03-06T08:01:44Z","action":"write","agent":"sensor-agent","target":"SQLite/sensor_readings","key":"HRV","old":null,"new":"47","source":"Ultrahuman API","verified":true}
{"ts":"2026-03-06T08:01:45Z","action":"ERROR","agent":"sensor-agent","target":"SQLite/sensor_readings","key":"weight","error":"ValidationError: write mismatch expected=82.3 got=null","source":"Withings API"}
```

**Cum folosești audit.log:**
- Dacă agentul zice că a actualizat ceva → verifici în audit.log
- Dacă nu e în log → nu s-a întâmplat
- Dacă e ERROR în log → știi exact ce a eșuat și când

---

## Nivelul 5 — Git ca version control pe workspace/

```bash
# Inițializare (o singură dată)
cd Desktop/medical-agent/workspace
git init
git add .
git commit -m "init: workspace setup"

# La fiecare modificare importantă (automat via sub-agenți):
git add MEMORY.md DATABASE/sqlite/medical.db
git commit -m "sync: [sursa] → [ce s-a schimbat] | $(date -u)"
```

**Beneficii:**
- Orice modificare are timestamp și mesaj
- Dacă agentul scrie ceva greșit → `git diff` arată exact ce
- `git log MEMORY.md` → istoricul complet al memoriei
- Rollback la orice stare anterioară în < 1 minut

---

## Nivelul 6 — Stale Thresholds (valori care expiră)

Valorile medicale nu sunt eterne. Dacă nu sunt reconfirmate în intervalul de mai jos → marcate automat `[STALE]`.

```python
STALE_THRESHOLDS = {
    # Analize sânge
    "default_lab":        90,   # zile
    "HbA1c":             90,
    "lipide":            90,
    "hormoni":           180,
    "vitamina_D":        90,
    "feritina":          90,
    "inflamatie":        60,    # CRP, IL-6 etc.

    # Senzori (date zilnice — stale dacă lipsesc mai mult de N zile)
    "HRV":               3,
    "somn":              3,
    "greutate":          7,
    "glicemie":          1,

    # Date statice
    "inaltime":          365,
    "genetica":          3650,  # 10 ani
}
```

---

## Nivelul 7 — Canary Values (detecție halucinare)

Valori de test cunoscute, plantate în sistem. La boot, agentul le interoghează.
Dacă returnează altceva → agentul halucinează, sesiunea se oprește.

```python
CANARY_VALUES = [
    {"table": "biomarkers", "key": "CANARY_TEST_001", "expected": "42.0"},
    {"file": "MEMORY.md",   "key": "CANARY_CHECKSUM", "expected": "<hash_cunoscut>"},
]

def check_canary() -> bool:
    for canary in CANARY_VALUES:
        result = read(canary["table"] or canary["file"], canary["key"])
        if result != canary["expected"]:
            raise HallucinationDetected(
                f"Canary failed: {canary['key']} expected={canary['expected']} got={result}"
            )
    return True
```

---

## Ce se întâmplă când o regulă NU e respectată

| Situație | Mecanism care prinde | Consecință |
|----------|---------------------|------------|
| Agentul zice "am scris" dar n-a scris | Audit log — lipsește înregistrarea | Eroare raportată la sesiunea următoare prin boot sync |
| Valoare halucinată în MEMORY.md | SQLite ≠ MEMORY.md → boot sync o suprarescrie | MEMORY.md corectat automat, discrepanța logată |
| Valoare scrisă greșit în SQLite | `validated_write()` → read-back mismatch | `ValidationError` → operație anulată, logată în audit |
| Date vechi prezentate ca actuale | Stale threshold depășit | Tag `[STALE:>Nzile]` aplicat automat |
| Sursă lipsă pe o valoare | Tag `[UNVERIFIED]` aplicat | Agentul nu poate cita valoarea ca fact |
| Halucinare completă (date inventate) | Canary values → mismatch | Sesiune oprită, Antonio notificat |
| Conflict între două surse | Regula conflictului → `[CONFLICT]` tag | Nu se folosește valoarea până la rezolvare manuală |

---

## Implementare — Ordine de prioritate

1. **`validated_write()`** — primul de implementat, cel mai mult impact
2. **Audit log** — append-only, zero overhead
3. **Session boot protocol** — sincronizare MEMORY.md ↔ SQLite la start
4. **Git pe workspace/** — zero cost, maxim de siguranță
5. **Confidence tags în MEMORY.md** — vizibilitate pentru Antonio
6. **Stale thresholds** — automatizat în sub-agenți
7. **Canary values** — ultimul, pentru detecție edge cases
