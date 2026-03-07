-- =============================================================================
-- foreverhuman.health — Seed Date Development
-- Creare clinică demo + admin user (parolă: Admin1234!)
-- Rulat automat de PostgreSQL după schema.sql la primul start
-- =============================================================================

-- Clinică demo
INSERT INTO public.clinics (id, name, slug, country, timezone, plan, is_active, settings)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Clinica Demo foreverhuman',
    'demo',
    'RO',
    'Europe/Bucharest',
    'standard',
    true,
    '{"llm_provider": "anthropic"}'
) ON CONFLICT (id) DO NOTHING;

-- Admin user
-- Parolă: Admin1234!  →  bcrypt hash generat cu rounds=12
INSERT INTO public.users (id, clinic_id, email, hashed_password, first_name, last_name, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'admin@foreverhuman.health',
    '$2b$12$jItlfuOf0jl1wl4uzzvWj.h314Hcqzt496uS0NtlbIqwp5EQPQKjK',
    'Admin',
    'foreverhuman',
    'clinic_admin',
    true
) ON CONFLICT (id) DO NOTHING;

-- Doctor demo
INSERT INTO public.users (id, clinic_id, email, hashed_password, first_name, last_name, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000001',
    'doctor@foreverhuman.health',
    '$2b$12$jItlfuOf0jl1wl4uzzvWj.h314Hcqzt496uS0NtlbIqwp5EQPQKjK',
    'Dr. Ion',
    'Ionescu',
    'doctor',
    true
) ON CONFLICT (id) DO NOTHING;
