# Medical Agent — Long-Term Memory

> **Convenție surse:**
> `[MANUAL]` — introdus direct de Antonio
> `[AUTO:ANALIZE]` — extras automat la procesarea analizelor
> `[AUTO:SENZORI]` — actualizat automat din Withings / Ultrahuman / Apple
> `[AUTO:CALCUL]` — calculat implicit de agent

> ⚠️ **Integritate date:** Orice valoare din acest fișier trebuie să aibă sursă verificabilă (fișier, tabelă SQLite, timestamp). Valorile fără sursă sunt tratate ca necunoscute, nu ca adevăruri. La fiecare scriere: read-back obligatoriu. La conflict între surse: raportează, nu decide singur. Detalii în `SOUL.md > Integritate Memorie & Anti-Halucinare`.

---

## Profil Pacient

| Câmp | Valoare | Sursă | Ultima actualizare |
|------|---------|-------|--------------------|
| Nume | Antonio | — | — |
| Sex | Masculin | — | — |
| Data nașterii | [YYYY-MM-DD] | `[MANUAL]` | — |
| Vârstă | *calculat automat din data nașterii* | `[AUTO:CALCUL]` | — |
| Înălțime | [cm] | `[MANUAL]` | — |
| Greutate curentă | [kg] | `[AUTO:SENZORI]` Withings | — |
| IMC | *calculat automat* | `[AUTO:CALCUL]` | — |

---

## Condiții Cronice / Diagnostice

> Sursa primară: `[AUTO:ANALIZE]` — extrase la procesarea fiecărui set de analize.
> Pot fi adăugate și manual dacă există diagnostice externe nescanate.

| Condiție | Severitate | Data diagnosticului | Sursă | Status |
|----------|------------|---------------------|-------|--------|
| — | — | — | — | — |

---

## Alergii & Intoleranțe

> Sursă: `[MANUAL]`

| Alergen / Substanță | Tip reacție | Severitate | Data identificării |
|--------------------|-------------|------------|-------------------|
| — | — | — | — |

---

## Medicamente Curente

> Sursă: `[MANUAL]` — actualizat la orice schimbare de prescripție.

| Medicament | Doză | Frecvență | Prescris de | De când | Motiv |
|------------|------|-----------|-------------|---------|-------|
| — | — | — | — | — | — |

---

## Suplimente Active

> Sursă: `[MANUAL]` — sincronizat cu `workspace/FARMACIE/INVENTAR/inventar.md`

| Supliment | Brand | Doză | Frecvență | Motiv / Obiectiv | De când |
|-----------|-------|------|-----------|-----------------|---------|
| — | — | — | — | — | — |

---

## Obiective Biohacking

> Sursă: `[MANUAL]` — revizuite trimestrial sau la schimbarea priorităților.

### Direcție generală
Optimizare pe direcția biohacking: longevitate, performanță cognitivă, compoziție corporală, calitate somn, rezistență metabolică.

### Obiective active
| Obiectiv | Metrică de succes | Termen | Status |
|----------|------------------|--------|--------|
| [obiectiv] | [cum măsori] | [când] | 🔄 Activ |

### Obiective finalizate
| Obiectiv | Rezultat | Data închiderii |
|----------|----------|----------------|
| — | — | — |

---

## Genetică

> Sursă: `[MANUAL]` — upload la primirea rezultatelor.

| Test | Provider | Data | Fișier | Status |
|------|----------|------|--------|--------|
| Test genetic | [Provider] | 2016 | `workspace/ANALIZE/ARHIVA/GENETICE/2016/` | ✅ Disponibil |
| Test genetic actualizat | [Provider] | 2026 (planificat) | — | 🔄 În așteptare |

### Variante relevante identificate
> Completat la procesarea rezultatelor genetice.

| Genă | Variantă | Implicație | Acțiune / Protocol |
|------|----------|------------|-------------------|
| — | — | — | — |

---

## Biomarkeri — Tendințe Cheie

> Sursă: `[AUTO:ANALIZE]` — actualizat la fiecare procesare de analize.
> Format valoare: `[valoare] [unitate]` | Trend: ↑ (crescut) ↓ (scăzut) → (stabil) vs. măsurătoarea anterioară.

### Hematologie
| Indicator | Ultima valoare | Data | Referință | Trend | Status |
|-----------|---------------|------|-----------|-------|--------|
| — | — | — | — | — | — |

### Biochimie / Metabolism
| Indicator | Ultima valoare | Data | Referință | Trend | Status |
|-----------|---------------|------|-----------|-------|--------|
| — | — | — | — | — | — |

### Hormoni
| Indicator | Ultima valoare | Data | Referință | Trend | Status |
|-----------|---------------|------|-----------|-------|--------|
| — | — | — | — | — | — |

### Markeri inflamatori & cardiovasculari
| Indicator | Ultima valoare | Data | Referință | Trend | Status |
|-----------|---------------|------|-----------|-------|--------|
| — | — | — | — | — | — |

### Vitamine & Minerale
| Indicator | Ultima valoare | Data | Referință | Trend | Status |
|-----------|---------------|------|-----------|-------|--------|
| — | — | — | — | — | — |

---

## Patterns Senzori

> Sursă: `[AUTO:SENZORI]` — actualizat săptămânal la review.

### Withings
- **Greutate medie (ultimele 30 zile):** — kg | Trend: —
- **Compoziție corporală:** grăsime —% | masă musculară — kg
- **Tensiune arterială medie:** — / — mmHg
- **Notă:**

### Ultrahuman
- **Recovery score mediu:** — /100
- **HRV mediu:** — ms | Trend: —
- **Somn mediu:** — h | Somn profund: — h
- **Glicemie (pattern dominant):** —
- **Notă:**

### Apple Health
- **Pași medii/zi:** —
- **VO2max estimat:** — ml/kg/min
- **Notă:**

---

## Intervenții & Rezultate

> Sursă: `[MANUAL]` + `[AUTO:ANALIZE]`
> Logat la orice schimbare de protocol: supliment nou, dietă, antrenament, medicament.

| Data | Intervenție | Motiv | Rezultat observat | Status |
|------|-------------|-------|------------------|--------|
| — | — | — | — | — |

---

## Red Flags

> Semnale care au necesitat sau necesită atenție imediată.

| Data | Indicator | Valoare | Acțiune luată | Status |
|------|-----------|---------|--------------|--------|
| — | — | — | — | — |

---

## Întrebări Deschise

> Ce urmărim să clarificăm la următoarea rundă de analize sau consultație.

- [ ] —
