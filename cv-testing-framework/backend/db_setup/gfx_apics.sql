CREATE TABLE vrl.gfx_apics (
    branch_id integer REFERENCES public.branch(id),
    hd_space double precision,
    id serial NOT NULL PRIMARY KEY,
    is_nightly boolean NOT NULL,
    job_id bigint NOT NULL, -- VRL serial
    machine_config_id integer REFERENCES public.machineconfig(id),
    notes_string text NOT NULL,
    option_string text NOT NULL,
    p4cl_id integer REFERENCES public.p4cl(id),
    subtest_set_id integer REFERENCES public.subtest_set(id),
    test_id integer REFERENCES public.tests(id),
    time_start timestamptz NOT NULL,
    time_stop timestamptz NOT NULL,
    total_score double precision NOT NULL,
    user_id integer REFERENCES public.ldap_user(id),
    UNIQUE(job_id)
);
ALTER TABLE vrl.gfx_apics OWNER to backend;
GRANT ALL ON TABLE vrl.gfx_apics TO backend;
GRANT SELECT ON TABLE vrl.gfx_apics TO backend_readonly;

-- Register test suite
INSERT INTO public.test_meta (system, name) VALUES ('vrl', 'gfx_apics');

-- Scrape for test_data.json
INSERT INTO public.test_scrapers (test_meta_id, scrape_tag, scrape_params, enabled)
    SELECT id, 'apic', '{"gg2pattern": "cv_apic_%%", "readJSON": true}'::jsonb, true FROM public.test_meta
    WHERE system = 'vrl' AND name = 'gfx_apics';

-- Denormal view. Given we follow naming conventions and layout conventions defined in our spreadsheet, we
-- should eventually be able to autogenerate this.
CREATE VIEW vrl.gfx_apics_denormal AS (
    SELECT gfx_apics.id,
        branch.name AS branch,
        branch.build AS build_type,
        gpus.board_name,
        gpus.name AS gpu_name,
        gpus.ram AS gpu_ram,
            CASE p4cl.virtual
                WHEN '-1'::integer THEN p4cl.cl::text
                ELSE concat(p4cl.cl, '.', p4cl.virtual)
            END AS changelist,
        machineconfig.name AS machine,
        machineconfig.cpu AS cpu_name,
        machineconfig.os,
        machineconfig.os_build,
        machineconfig.ram AS cpu_ram,
        machineconfig.cpu_speed,
        tests.name AS test_name,
        ldap_user.ldap_name AS "user",
        gfx_apics.time_start,
        gfx_apics.time_stop,
        gfx_apics.job_id AS vrl_serial,
        gfx_apics.is_nightly,
        gfx_apics.option_string,
        gfx_apics.hd_space,
        gfx_apics.total_score,
        gfx_apics.subtest_set_id
    FROM vrl.gfx_apics
        JOIN branch ON branch.id = gfx_apics.branch_id
        JOIN p4cl ON p4cl.id = gfx_apics.p4cl_id
        JOIN machineconfig ON machineconfig.id = gfx_apics.machine_config_id
        JOIN gpus ON gpus.id = machineconfig.gpu_id
        JOIN tests ON tests.id = gfx_apics.test_id
        JOIN ldap_user ON ldap_user.id = gfx_apics.user_id
);
ALTER TABLE vrl.gfx_apics_denormal OWNER to backend;
GRANT ALL ON TABLE vrl.gfx_apics_denormal TO backend;
GRANT SELECT ON TABLE vrl.gfx_apics_denormal TO backend_readonly;