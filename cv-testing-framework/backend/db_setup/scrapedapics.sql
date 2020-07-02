-- Get scraped apic data for testing. This is real data, but not for use
-- in production.

-- This is the SQL involved in adding a test. It mostly involves
-- creating the table with apropriate fields, adding permissions,
-- and adding some entries that in some top level tables that
-- this is a test suite. This should eventually be automated via a wizard
-- and user interface of some kind, which let someone pick columns to add, as
-- well
CREATE TABLE vrl.apics (
    id serial NOT NULL PRIMARY KEY,
    branch text,
    changelist text NOT NULL,
    total_score double precision NOT NULL,
    subtest_results jsonb NOT NULL,
    cpu text NOT NULL,
    gpu text NOT NULL,
    os text NOT NULL,
    machine text NOT NULL,
    original_id text NOT NULL,
    status text NOT NULL,
    time_start timestamptz NOT NULL,
    time_stop timestamptz NOT NULL,
    notes text NOT NULL,
    "group" text NOT NULL,
    UNIQUE(original_id)
);
ALTER TABLE vrl.apics OWNER to backend;
GRANT ALL ON TABLE vrl.apics TO backend;
GRANT SELECT ON TABLE vrl.apics TO backend_readonly;
-- Register test suite
INSERT INTO public.test_meta (system, name) VALUES ('vrl', 'apics');
-- Add scraper (percent needs to be escaped).
INSERT INTO public.test_scrapers (test_meta_id, scrape_tag, scrape_params, enabled)
    SELECT id, 'apic', '{"gg2pattern": "cv_apic_%%"}'::jsonb, true FROM public.test_meta
    WHERE system = 'vrl' AND name = 'apics';