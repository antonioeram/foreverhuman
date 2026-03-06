# sensor-agent — Config

**Rol:** Colectează date biologice de la senzori prin API. Salvează .md + ingestează în SQLite + LanceDB.

---

## Surse & Cron

| Sursă | Cron | Endpoint principal |
|-------|------|--------------------|
| Withings | `0 8,12,23 * * *` | `https://wbsapi.withings.net/v2/measure` |
| Ultrahuman | `0 8,12,17,23 * * *` | Ultrahuman API |
| Apple Health | manual (export XML) | HealthKit export |

---

## Withings — Date extrase

| Metric | Tip măsurătoare | Unitate |
|--------|----------------|---------|
| Greutate | `meastype=1` | kg |
| Masă grasă % | `meastype=6` | % |
| Masă musculară | `meastype=76` | kg |
| Apă corporală % | `meastype=77` | % |
| Tensiune sistolică | `meastype=9` | mmHg |
| Tensiune diastolică | `meastype=10` | mmHg |
| Puls | `meastype=11` | bpm |
| Somn (durata, faze, HRV, RHR) | Sleep API | min / ms / bpm |

## Ultrahuman — Date extrase
- Recovery score (0-100)
- HRV (ms)
- Somn total, profund, REM (min)
- Resting heart rate (bpm)
- Glicemie (mg/dL) — dacă Ring Air conectat
- Activitate: pași, calorii active

## Apple Health — Date extrase (la sync manual)
- Pași zilnici
- VO2max estimat (ml/kg/min)
- Frecvență cardiacă medie
- Calorii active

---

## Credentials (`.env`)
```
WITHINGS_CLIENT_ID=
WITHINGS_CLIENT_SECRET=
WITHINGS_ACCESS_TOKEN=
WITHINGS_REFRESH_TOKEN=
ULTRAHUMAN_API_KEY=
```

---

## Output

### .md output path
```
workspace/SENZORI/[DEVICE]/ARHIVA/[YYYY]/[MM]/[YYYY-MM-DD].md
```

### Format .md generat
```markdown
# [Device] — [YYYY-MM-DD]

## Date colectate
| Metric | Valoare | Unitate | Timestamp |
|--------|---------|---------|-----------|
| ...    | ...     | ...     | ...       |

## Note agent
[Anomalii detectate, valori în afara range-ului normal]
```

---

## SQLite — Tabele scrise
- `sensor_readings` — toate valorile brute
- `sleep_log` — date somn agregate per zi
- `body_composition` — compoziție corporală

## LanceDB — Tabel scris
- `daily_observations` — embedding pe textul narativ din .md

---

## Logică de alertă
Dacă oricare valoare depășește threshold-urile de mai jos → scrie în `MEMORY.md > Red Flags` + notifică Main Agent:

| Metric | Red Flag |
|--------|----------|
| HRV | < 20 ms (3 zile consecutive) |
| Recovery score | < 30 (2 zile consecutive) |
| Tensiune sistolică | > 140 mmHg |
| Glicemie | > 180 mg/dL post-prandial |
| Greutate | variație > 2 kg în 24h |
