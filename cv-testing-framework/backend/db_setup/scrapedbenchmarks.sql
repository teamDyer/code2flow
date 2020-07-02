CREATE TABLE vrl.benchmarks (
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
ALTER TABLE vrl.benchmarks OWNER to backend;
GRANT ALL ON TABLE vrl.benchmarks TO backend;
GRANT SELECT ON TABLE vrl.benchmarks TO backend_readonly;
-- Register test suite
INSERT INTO public.test_meta (system, name) VALUES ('vrl', 'benchmarks');
-- Add scraper (percent needs to be escaped).
INSERT INTO public.test_scrapers (test_meta_id, scrape_tag, scrape_params, enabled)
    SELECT id, 'apic', '{"gg2pattern": "cv_benchmark_%%"}'::jsonb, true FROM public.test_meta
    WHERE system = 'vrl' AND name = 'benchmarks';