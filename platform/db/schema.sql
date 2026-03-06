-- =============================================================================
-- foreverhuman.health — PostgreSQL Schema
-- Version: 0.1.0 | 2026-03
-- =============================================================================
-- Arhitectura multi-tenant:
--   schema public        → clinici, doctori, accounts (shared)
--   schema patient_{uuid} → datele izolate ale unui pacient
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- full-text search pe analize

-- =============================================================================
-- SCHEMA PUBLIC — Multi-tenant shared
-- =============================================================================

-- Clinici
CREATE TABLE public.clinics (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,        -- folosit ca prefix în URL
    country     VARCHAR(2)   NOT NULL DEFAULT 'RO',  -- ISO 3166-1 alpha-2
    timezone    VARCHAR(50)  NOT NULL DEFAULT 'Europe/Bucharest',
    plan        VARCHAR(50)  NOT NULL DEFAULT 'standard', -- standard / premium / enterprise
    is_active   BOOLEAN      NOT NULL DEFAULT true,
    settings    JSONB        NOT NULL DEFAULT '{}',  -- config per clinică (llm_provider, ollama_url, etc.)
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Utilizatori (doctori, admini, platformă)
CREATE TABLE public.users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id       UUID REFERENCES public.clinics(id) ON DELETE CASCADE,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    role            VARCHAR(50)  NOT NULL CHECK (role IN ('doctor', 'clinic_admin', 'platform_admin')),
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_clinic_id ON public.users(clinic_id);
CREATE INDEX idx_users_email     ON public.users(email);

-- Pacienți (înregistrare separată — nu sunt users cu login direct inițial)
CREATE TABLE public.patients (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id       UUID NOT NULL REFERENCES public.clinics(id) ON DELETE CASCADE,
    email           VARCHAR(255),
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    date_of_birth   DATE,
    sex             CHAR(1) CHECK (sex IN ('M', 'F', 'O')),
    phone           VARCHAR(30),
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    schema_name     VARCHAR(100) GENERATED ALWAYS AS ('patient_' || replace(id::text, '-', '_')) STORED,
    consent_at      TIMESTAMPTZ,                          -- momentul consimțământului explicit
    consent_version VARCHAR(20),                          -- versiunea doc acceptat
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_patients_clinic_id ON public.patients(clinic_id);

-- Asociere doctor ↔ pacient (opțional — pentru tracking, nu pentru acces)
-- Accesul e la nivel de clinică, nu individual; această tabelă e pentru "medicul de referință"
CREATE TABLE public.doctor_patient_assignments (
    doctor_id   UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    patient_id  UUID NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (doctor_id, patient_id)
);

-- Refresh tokens (JWT rotation)
CREATE TABLE public.refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES public.users(id) ON DELETE CASCADE,
    patient_id  UUID REFERENCES public.patients(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ  NOT NULL,
    revoked     BOOLEAN      NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (
        (user_id IS NOT NULL AND patient_id IS NULL) OR
        (user_id IS NULL AND patient_id IS NOT NULL)
    )
);
CREATE INDEX idx_refresh_tokens_hash ON public.refresh_tokens(token_hash);

-- Consent log (GDPR Art. 7)
CREATE TABLE public.consent_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id      UUID NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,
    consent_type    VARCHAR(100) NOT NULL,  -- 'main', 'outcome_vectors', 'sensor_X'
    granted         BOOLEAN      NOT NULL,
    ip_address      INET,
    user_agent      TEXT,
    doc_version     VARCHAR(20),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_consent_log_patient ON public.consent_log(patient_id, consent_type);

-- =============================================================================
-- FUNCȚIE: Creare schema per pacient
-- Apelată după INSERT în public.patients
-- =============================================================================

CREATE OR REPLACE FUNCTION create_patient_schema(p_patient_id UUID)
RETURNS VOID AS $$
DECLARE
    schema_nm TEXT := 'patient_' || replace(p_patient_id::text, '-', '_');
BEGIN
    -- Creare schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_nm);

    -- Profile
    EXECUTE format('
        CREATE TABLE %I.profile (
            key         VARCHAR(100) PRIMARY KEY,
            value       TEXT,
            source      VARCHAR(50) DEFAULT ''[MANUAL]'',
            confidence  VARCHAR(20) DEFAULT ''[UNVERIFIED]'',
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);

    -- Biomarkeri (analize laborator)
    EXECUTE format('
        CREATE TABLE %I.biomarkers (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name        VARCHAR(100) NOT NULL,
            value       NUMERIC,
            unit        VARCHAR(30),
            ref_min     NUMERIC,
            ref_max     NUMERIC,
            lab_name    VARCHAR(100),
            source_file VARCHAR(255),
            tested_at   DATE NOT NULL,
            confidence  VARCHAR(20) NOT NULL DEFAULT ''[VERIFIED]'',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);
    EXECUTE format('CREATE INDEX ON %I.biomarkers(name, tested_at DESC)', schema_nm);

    -- Date senzori
    EXECUTE format('
        CREATE TABLE %I.sensor_readings (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            source      VARCHAR(50) NOT NULL,   -- withings, ultrahuman, apple_health
            metric      VARCHAR(100) NOT NULL,  -- HRV, weight, sleep_score, etc.
            value       NUMERIC,
            value_json  JSONB,                  -- pentru valori complexe (sleep stages)
            unit        VARCHAR(30),
            recorded_at TIMESTAMPTZ NOT NULL,
            confidence  VARCHAR(20) NOT NULL DEFAULT ''[VERIFIED]'',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);
    EXECUTE format('CREATE INDEX ON %I.sensor_readings(metric, recorded_at DESC)', schema_nm);
    EXECUTE format('CREATE INDEX ON %I.sensor_readings(source, recorded_at DESC)', schema_nm);

    -- Suplimente curente
    EXECUTE format('
        CREATE TABLE %I.supplements (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name        VARCHAR(200) NOT NULL,
            dose        VARCHAR(100),
            frequency   VARCHAR(100),
            reason      TEXT,
            started_at  DATE,
            stopped_at  DATE,
            source      VARCHAR(50) DEFAULT ''[MANUAL]'',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);

    -- Medicamente curente
    EXECUTE format('
        CREATE TABLE %I.medications (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name        VARCHAR(200) NOT NULL,
            dose        VARCHAR(100),
            frequency   VARCHAR(100),
            prescribed_by VARCHAR(100),
            started_at  DATE,
            stopped_at  DATE,
            source      VARCHAR(50) DEFAULT ''[MANUAL]'',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);

    -- Jurnale zilnice
    EXECUTE format('
        CREATE TABLE %I.daily_logs (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            log_date    DATE NOT NULL UNIQUE,
            energy      SMALLINT CHECK (energy BETWEEN 1 AND 10),
            mood        SMALLINT CHECK (mood BETWEEN 1 AND 10),
            stress      SMALLINT CHECK (stress BETWEEN 1 AND 10),
            notes       TEXT,
            raw_input   TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);

    -- Directive doctor → agent pacient
    EXECUTE format('
        CREATE TABLE %I.directives (
            id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            doctor_id       UUID NOT NULL,           -- referință la public.users
            directive_type  VARCHAR(50) NOT NULL,    -- protocol_change, flag, note, recommendation
            content         JSONB NOT NULL,
            status          VARCHAR(30) NOT NULL DEFAULT ''pending'',
            patient_notified BOOLEAN NOT NULL DEFAULT false,
            agent_applied   BOOLEAN NOT NULL DEFAULT false,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            applied_at      TIMESTAMPTZ
        )', schema_nm);

    -- Memory agent (MEMORY.md backup în DB)
    EXECUTE format('
        CREATE TABLE %I.agent_memory (
            key         VARCHAR(100) PRIMARY KEY,
            value       TEXT,
            confidence  VARCHAR(20) NOT NULL DEFAULT ''[VERIFIED]'',
            source      VARCHAR(255),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )', schema_nm);

    -- Audit log (append-only — nu se face DELETE sau UPDATE)
    EXECUTE format('
        CREATE TABLE %I.audit_log (
            id          BIGSERIAL PRIMARY KEY,
            ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            action      VARCHAR(30) NOT NULL,    -- write, read, delete, error, boot_sync
            agent       VARCHAR(50),             -- main, sensor-agent, etc.
            target      VARCHAR(100),            -- tabelă sau fișier
            key_name    VARCHAR(100),
            old_value   TEXT,
            new_value   TEXT,
            source      TEXT,
            verified    BOOLEAN,
            error_msg   TEXT
        )', schema_nm);
    -- Index descendent pe timp pentru căutare rapidă în log
    EXECUTE format('CREATE INDEX ON %I.audit_log(ts DESC)', schema_nm);

    -- Canary values (detecție halucinare)
    EXECUTE format('
        CREATE TABLE %I.canary_values (
            key         VARCHAR(100) PRIMARY KEY,
            expected    TEXT NOT NULL,
            description VARCHAR(255)
        )', schema_nm);
    EXECUTE format('
        INSERT INTO %I.canary_values(key, expected, description) VALUES
            (''CANARY_001'', ''42.0'', ''Biomarker test constant''),
            (''CANARY_002'', ''foreverhuman_v1'', ''System identity check'')',
        schema_nm);

    -- Memory confidence tracking
    EXECUTE format('
        CREATE TABLE %I.memory_confidence (
            field       VARCHAR(100) PRIMARY KEY,
            tag         VARCHAR(20)  NOT NULL DEFAULT ''[UNVERIFIED]'',
            last_verified TIMESTAMPTZ,
            stale_after_days INTEGER
        )', schema_nm);

END;
$$ LANGUAGE plpgsql;

-- Trigger automat: creare schema când se adaugă un pacient
CREATE OR REPLACE FUNCTION trigger_create_patient_schema()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM create_patient_schema(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_patient_insert
    AFTER INSERT ON public.patients
    FOR EACH ROW
    EXECUTE FUNCTION trigger_create_patient_schema();

-- =============================================================================
-- SCHEMA KB — Knowledge Base (pe serverul central, schema separată)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS kb;

-- Articole ingerate
CREATE TABLE kb.articles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL,   -- pubmed, youtube, web, book
    source_id   VARCHAR(255),           -- PMID, YouTube video ID, URL, ISBN
    title       TEXT NOT NULL,
    authors     TEXT[],
    published_at DATE,
    url         TEXT,
    abstract    TEXT,
    full_text   TEXT,
    language    VARCHAR(10) DEFAULT 'en',
    tags        TEXT[],
    quality_score NUMERIC(3,2),         -- 0.00 – 1.00
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_type, source_id)
);
CREATE INDEX ON kb.articles USING gin(tags);
CREATE INDEX ON kb.articles(source_type, published_at DESC);

-- Outcome vectors anonimizate (opt-in)
CREATE TABLE kb.outcome_vectors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intervention    VARCHAR(200) NOT NULL,   -- "Magnesium glycinate 400mg"
    outcome_metric  VARCHAR(100) NOT NULL,   -- "HRV"
    baseline_value  NUMERIC,
    outcome_value   NUMERIC,
    duration_days   INTEGER,
    sex             CHAR(1),
    age_group       VARCHAR(20),             -- "30-35" — nu vârsta exactă
    anonymized_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ingestor jobs (monitorizare pipeline)
CREATE TABLE kb.ingestor_jobs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingestor    VARCHAR(50) NOT NULL,    -- pubmed, youtube, web, library
    status      VARCHAR(30) NOT NULL DEFAULT 'pending',
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    articles_ingested INTEGER DEFAULT 0,
    error_msg   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- VIEWS utile
-- =============================================================================

-- Număr pacienți activi per clinică
CREATE VIEW public.clinic_stats AS
SELECT
    c.id,
    c.name,
    c.slug,
    COUNT(DISTINCT p.id) FILTER (WHERE p.is_active) AS active_patients,
    COUNT(DISTINCT u.id) FILTER (WHERE u.role = 'doctor' AND u.is_active) AS active_doctors,
    c.plan,
    c.created_at
FROM public.clinics c
LEFT JOIN public.patients p ON p.clinic_id = c.id
LEFT JOIN public.users u ON u.clinic_id = c.id
GROUP BY c.id, c.name, c.slug, c.plan, c.created_at;

-- =============================================================================
-- FUNCȚIE: Cascade delete pacient (GDPR Art. 17)
-- =============================================================================

CREATE OR REPLACE FUNCTION delete_patient_gdpr(p_patient_id UUID)
RETURNS VOID AS $$
DECLARE
    schema_nm TEXT := 'patient_' || replace(p_patient_id::text, '-', '_');
BEGIN
    -- Șterge schema și tot ce conține
    EXECUTE format('DROP SCHEMA IF EXISTS %I CASCADE', schema_nm);

    -- Șterge din public
    DELETE FROM public.consent_log WHERE patient_id = p_patient_id;
    DELETE FROM public.refresh_tokens WHERE patient_id = p_patient_id;
    DELETE FROM public.doctor_patient_assignments WHERE patient_id = p_patient_id;
    DELETE FROM public.patients WHERE id = p_patient_id;

    RAISE NOTICE 'GDPR delete completed for patient %', p_patient_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Row-Level Security
-- =============================================================================

-- Activare RLS pe tabele critice
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Politică: utilizatorul vede DOAR pacienții clinicii sale
-- (se aplică după setarea variabilei de sesiune app.current_clinic_id)
CREATE POLICY clinic_isolation_patients ON public.patients
    USING (clinic_id = current_setting('app.current_clinic_id')::UUID);

CREATE POLICY clinic_isolation_users ON public.users
    USING (clinic_id = current_setting('app.current_clinic_id')::UUID);

-- =============================================================================
-- Date inițiale
-- =============================================================================

-- Clinică demo (pentru development/testing)
INSERT INTO public.clinics (id, name, slug, country, plan)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Demo Clinic',
    'demo',
    'RO',
    'standard'
) ON CONFLICT DO NOTHING;
