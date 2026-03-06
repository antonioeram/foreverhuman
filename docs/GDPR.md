# GDPR — foreverhuman.health

Conformitate GDPR pentru deployment self-hosted în Romania/UE. Actualizat: 2026-03.

> **Disclaimer:** Acest document nu înlocuiește consultanța juridică. Pentru o clinică reală,
> consultați un avocat specializat înainte de a procesa date medicale de la pacienți.

---

## Temeiul Legal

**Articol 9 GDPR** — Date speciale (categorii sensibile), inclusiv date de sănătate.

Temeiuri aplicabile:
- **Art. 9(2)(a)** — Consimțământ explicit al persoanei vizate (pacient)
- **Art. 9(2)(h)** — Scop medical, cu obligație de confidențialitate

**Categorizare produs:** Wellness / biohacking (nu dispozitiv medical). Evită regimul MDR (Medical Device Regulation) și FDA dacă nu se emit diagnostice formale sau recomandări de tratament medicamentos.

---

## Principii Implementate (Art. 5 GDPR)

| Principiu | Implementare concretă |
|-----------|----------------------|
| **Lawfulness** | Consimțământ explicit la înrolare + reînnoire anuală |
| **Purpose limitation** | Date pacient folosite DOAR pentru serviciul acelui pacient |
| **Data minimisation** | Colectăm doar ce e necesar pentru funcționalitate |
| **Accuracy** | Stale thresholds + validated_write() asigură date actualizate |
| **Storage limitation** | Retenție configurabilă per clinică; delete la cerere |
| **Integrity & confidentiality** | Izolare VM per clinică, RLS PostgreSQL, JWT auth |
| **Accountability** | Audit log append-only, DPA documentat |

---

## Drepturi Pacienți (Art. 15–22)

### Dreptul de acces (Art. 15)
**Implementare:** Endpoint `GET /api/v1/me/export`
- Returnează toate datele pacientului în format JSON
- Include: profil, analize, date senzori, jurnale, memory agent
- Timp răspuns: < 30 zile (obligatoriu GDPR), target < 24h

### Dreptul la rectificare (Art. 16)
**Implementare:** Pacientul poate edita datele de profil prin app
- Modificările se propagă prin `validated_write()` → audit_log

### Dreptul la ștergere (Art. 17)
**Implementare:** Endpoint `DELETE /api/v1/me` → cascade delete
```sql
-- Exemplu cascade delete pentru patient_{uuid} schema
DROP SCHEMA patient_{uuid} CASCADE;
-- Șterge din: profiles, biomarkers, sensor_readings, daily_logs,
--             supplements, directives, audit_log (specific patient)
-- Șterge namespace LanceDB: patient_{uuid}
-- Șterge fișiere: workspace/PACIENȚI/{uuid}/
```
**Excepție:** Datele anonimizate deja contribute la KB central (opt-in) nu pot fi șterse — pacientul este informat la momentul opt-in.

### Dreptul la portabilitate (Art. 20)
**Implementare:** Același endpoint export (`/me/export`) returnează JSON structurat, importabil în alte sisteme.

### Dreptul la opoziție (Art. 21)
**Implementare:** Pacientul poate dezactiva oricând:
- Opt-in outcome vectors (din settings app)
- Procesare date senzori specifici

### Dreptul la restricționarea procesării (Art. 18)
**Implementare:** Contul poate fi pus în stare `suspended` — date păstrate, nu procesate activ.

---

## Consimțământ

### La înrolare (onboarding)
- [ ] Pacientul acceptă explicit Termeni + Politică Confidențialitate
- [ ] Consimțământ separat pentru fiecare categorie de date sensibile
- [ ] Consimțământ separat pentru opt-in outcome vectors (KB)
- [ ] Log consimțământ cu timestamp + IP + versiunea documentelor acceptate
- [ ] Posibilitate retragere consimțământ oricând din app

### Reînnoire
- Consimțământul se reconfirmă anual sau la modificare substanțială a politicii
- Notificare push + email cu 30 zile înainte

### Format consimțământ
```
☐ Accept că foreverhuman procesează datele mele de sănătate (analize, senzori, jurnal)
  pentru a-mi furniza serviciul de monitoring personal. [obligatoriu]

☐ Sunt de acord ca datele mele ANONIMIZATE (fără nume, fără identificatori) să fie
  contribute la knowledge base pentru îmbunătățirea recomandărilor generale. [opțional]
```

---

## Arhitectura din perspectiva GDPR

### Izolare date
```
KB Central Server (EU)
  └── ZERO date pacienți identificabile
  └── Conține DOAR: articole, meta-analize, cărți, vectori outcome ANONIMIZAȚI

Clinică VM (România / EU)
  └── PostgreSQL: date pacienți — nu iese din VM
  └── LanceDB: vectori pacienți — nu iese din VM
  └── Backup criptat local sau S3 în EU (eu-central-1)
  └── Acces extern: ZERO (API privat, fără endpoint public pentru DB)
```

### Transfer date internaționale
- **Claude API (Anthropic, US):** Datele trimise pentru inferență includ contextul conversației.
  - **Mitigare:** Prompturile nu includ date direct identificabile (PII) — se folosesc ID-uri interne.
  - **DPA Anthropic:** https://www.anthropic.com/legal/data-processing-addendum
  - **Alternativă privacy-maximă:** Ollama local — zero date externe.
- **OpenAI Embeddings API:** Textul medical este trimis pentru embedding.
  - **Mitigare:** Optim Ollama embeddings pentru clinici cu cerințe de privacy maximă.
  - **DPA OpenAI:** disponibil pe platform.openai.com

### Pseudonimizare
- Pacienții sunt referinți intern prin `patient_uuid` — nu nume
- Datele trimise la API-uri externe nu conțin PII (nume, CNP, adresă)
- Analizele de laborator sunt procesate după extragerea valorilor numerice, nu ca imagini

---

## Operator de Date / Responsabil cu Protecția Datelor

### Operatorul de date
- **Clinica** este operator de date pentru pacienții săi
- **foreverhuman** este împuternicit al operatorului (processor)
- Contractul de procesare (DPA) se semnează cu fiecare clinică

### DPO (Data Protection Officer)
- Obligatoriu conform Art. 37 GDPR dacă procesarea e la scară largă
- Pentru clinici mici (< 250 angajați, < ~500 pacienți): DPO recomandat, nu obligatoriu
- Pentru platformă (foreverhuman ca entitate): evaluare la 1000+ pacienți activi

### Registrul activităților (Art. 30)
Fiecare clinică menține registrul:

```
Activitate: Monitorizare stare de sănătate pacienți
Scopul: Furnizare serviciu wellness personalizat
Categorii de date: date de sănătate (analize, senzori), date de contact
Categorii de persoane vizate: pacienți adulți
Destinatari: medici din clinică, agentul AI intern
Transfer terțe țări: Claude API (US) — cu DPA; OpenAI API (US) — cu DPA
Termen de păstrare: durata contractului + 3 ani (sau la cerere de ștergere)
Măsuri tehnice: criptare în tranzit (TLS 1.3), criptare la repaus (volum criptat)
```

---

## Securitate Tehnică (Art. 32)

### Implementate
- [ ] TLS 1.3 pe toate conexiunile (nginx + Let's Encrypt)
- [ ] JWT cu expiry scurt (15 min access token)
- [ ] Refresh token rotation
- [ ] Parole hash cu bcrypt (cost factor ≥ 12)
- [ ] RLS PostgreSQL — doctor nu poate accesa altă clinică
- [ ] Audit log append-only (detectare acces neautorizat)
- [ ] Backup criptat (volume criptat sau pgcrypto)

### De implementat
- [ ] Rate limiting pe autentificare (max 5 încercări / 15 min)
- [ ] 2FA opțional (TOTP) pentru conturi doctor/admin
- [ ] Notificare automată la login nou din IP necunoscut
- [ ] Penetration test anual

### Breach Notification (Art. 33-34)
- Breach detectat → notificare ANSPDCP (autoritatea română) în < 72h
- Dacă risc ridicat pentru persoane → notificare directă pacienți
- Template notificare breach disponibil în `docs/templates/breach-notification.md`

---

## Retenție Date

| Categorie | Retenție | Motiv |
|-----------|----------|-------|
| Date pacient activ | Durata contract | Serviciu activ |
| Date pacient după reziliere | 3 ani | Obligații legale potențiale |
| Audit log | 5 ani | Detectare incidente retroactivă |
| Date anonimizate KB | Nedefinit | Nu mai sunt date personale |
| Backup-uri | 30 zile rolling | Recovery operațional |

---

## Checklist Pre-Launch per Clinică

- [ ] DPA semnat între clinică și foreverhuman
- [ ] Politică confidențialitate publicată (link în app)
- [ ] Termeni și condiții publicați
- [ ] Registru activități completat
- [ ] Consimțământ flow testat end-to-end
- [ ] Export date testat (`GET /me/export`)
- [ ] Delete cascade testat (`DELETE /me`)
- [ ] Backup criptat configurat și testat (restore drill)
- [ ] TLS valid (cert Let's Encrypt, auto-renew)
- [ ] DPA cu Anthropic acceptat (dacă se folosește Claude API)
- [ ] DPA cu OpenAI acceptat (dacă se folosesc embeddings OpenAI)
- [ ] Notificat ANSPDCP dacă obligatoriu (clinici mari)

---

## Resurse

- GDPR full text: https://gdpr-info.eu/
- ANSPDCP (autoritatea română): https://www.dataprotection.ro/
- Ghid EDPB pentru aplicații de sănătate: https://edpb.europa.eu/
- Anthropic DPA: https://www.anthropic.com/legal/data-processing-addendum
