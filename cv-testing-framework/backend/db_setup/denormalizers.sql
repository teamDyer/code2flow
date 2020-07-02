-- This file contains definitions for a number of tables that
-- are used for denormalizing input data for many tests.
-- A test will push data to the hub in a form
-- branch,gpu_name,gpu_speed,user,gpu_ram,cpu_ram,etc.
-- and this will be denormalized (in some cases) to a row
-- in a test table like
-- branch_id,machine_config_id,score
-- This saves space in our database and makes some kinds of queries easier/faster.
-- On the other hand, having the normalized view is easier/faster in other cases, such as
-- writing analyical queries.

-- Branches table (perforce branches)
CREATE TABLE public.branch (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    build text NOT NULL,
    UNIQUE(name, build)
);
ALTER TABLE public.branch OWNER to backend;
GRANT ALL ON TABLE public.branch TO backend;
GRANT SELECT ON TABLE public.branch TO backend_readonly;

-- GPUs table
CREATE TABLE public.gpus (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    ram integer NOT NULL,
    vbios text NOT NULL,
    board_name text NOT NULL,
    UNIQUE(name, ram, vbios, board_name)
);
ALTER TABLE public.gpus OWNER to backend;
GRANT ALL ON TABLE public.gpus TO backend;
GRANT SELECT ON TABLE public.gpus TO backend_readonly;

--  Job Audit table (for logging repeated requests)
CREATE TABLE public.job_audit (
    data_hash TEXT NOT NULL PRIMARY KEY,
    data jsonb NOT NULL,
    attempts integer NOT NULL,
    UNIQUE(data_hash)
);
ALTER TABLE public.job_audit OWNER to backend;
GRANT ALL ON TABLE public.job_audit TO backend;
GRANT SELECT ON TABLE public.job_audit TO backend_readonly;

-- LDAP users (track some information about users obtained over LDAP)
CREATE TABLE public.ldap_user (
    id serial NOT NULL PRIMARY KEY,
    ldap_name text NOT NULL,
    email text NOT NULL,
    UNIQUE(ldap_name)
);
ALTER TABLE public.ldap_user OWNER to backend;
GRANT ALL ON TABLE public.ldap_user TO backend;
GRANT SELECT ON TABLE public.ldap_user TO backend_readonly;

-- Machine Config table
CREATE TABLE public.machineconfig (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    gpu_id integer NOT NULL REFERENCES public.gpus(id),
    cpu text NOT NULL,
    os text NOT NULL,
    os_build text NOT NULL,
    ram integer NOT NULL,
    cpu_speed text NOT NULL,
    UNIQUE(name, gpu_id, cpu, os, os_build, ram, cpu_speed)
);
ALTER TABLE public.machineconfig OWNER to backend;
GRANT ALL ON TABLE public.machineconfig TO backend;
GRANT SELECT ON TABLE public.machineconfig TO backend_readonly;

-- P4CL table (perforce changelists)
CREATE TABLE public.p4cl (
    id serial NOT NULL PRIMARY KEY,
    cl bigint NOT NULL,
    virtual integer NOT NULL,
    UNIQUE(cl, virtual)
);
ALTER TABLE public.p4cl OWNER to backend;
GRANT ALL ON TABLE public.p4cl TO backend;
GRANT SELECT ON TABLE public.p4cl TO backend_readonly;

-- Subtest set (grouping subtests together). This is just used as a unique identifier.
CREATE TABLE public.subtest_set (
    id serial NOT NULL PRIMARY KEY
);
ALTER TABLE public.subtest_set OWNER to backend;
GRANT ALL ON TABLE public.subtest_set TO backend;
GRANT SELECT ON TABLE public.subtest_set TO backend_readonly;

-- Subtest scores (for apic style VRL tests). This provides some more structure to the subtest
-- scores submitted by apics and benchmarks to make more efficient queries possible.
CREATE TABLE public.subtest_scores (
    job_id integer NOT NULL PRIMARY KEY,
    subtest_id integer NOT NULL REFERENCES public.subtest_set(id),
    score double precision,
    functional_result integer,
    evo_scores jsonb,
    functional_threshold double precision,
    functional_delta double precision,
    UNIQUE(job_id, subtest_id, score, functional_result, evo_scores, functional_threshold, functional_delta)
);
ALTER TABLE public.subtest_scores OWNER to backend;
GRANT ALL ON TABLE public.subtest_scores TO backend;
GRANT SELECT ON TABLE public.subtest_scores TO backend_readonly;

-- Tests (apic style test results). This just keeps a set of VRL testnames (interns strings).
CREATE TABLE public.tests (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    UNIQUE(name)
);
ALTER TABLE public.tests OWNER TO backend;
GRANT ALL ON TABLE public.tests TO backend;
GRANT SELECT ON TABLE public.tests TO backend_readonly;

-- Subtests (apic style test results). This just keeps a set of apic subtest names (interns strings).
CREATE TABLE public.subtests (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    UNIQUE(name)
);
ALTER TABLE public.subtests OWNER to backend;
GRANT ALL ON TABLE public.subtests TO backend;
GRANT SELECT ON TABLE public.subtests TO backend_readonly;

-- Test Systems Table. This just keeps a set of test systems (VRL, cvcServer)
CREATE TABLE public.test_systems
(
    id integer NOT NULL PRIMARY KEY,
    name text NOT NULL,
    UNIQUE(name)
)
ALTER TABLE public.test_systems OWNER to backend;
GRANT ALL ON TABLE public.test_systems TO backend;
GRANT ALL ON TABLE public.test_systems TO backend_readonly;

-- Test Systems Mapping Table. This keeps mapping of test system vs test ids
CREATE TABLE public.test_system_mapping
(
    test_id integer NOT NULL REFERENCES public.tests(id),
    system_id integer NOT NULL REFERENCES public.test_systems(id),
    UNIQUE(test_id, system_id)
)
ALTER TABLE public.test_system_mapping OWNER to backend;
GRANT ALL ON TABLE public.test_system_mapping TO backend;
GRANT ALL ON TABLE public.test_system_mapping TO backend_readonly;

-- Machine Pool Table. This just keeps set of machine pools.
CREATE TABLE public.machine_pools
(
    id integer NOT NULL PRIMARY KEY,
    name text NOT NULL,
    UNIQUE(name)
)
ALTER TABLE public.machine_pools OWNER to backend;
GRANT ALL ON TABLE public.machine_pools TO backend;
GRANT ALL ON TABLE public.machine_pools TO backend_readonly;

-- Machine System Mapping Table. This just keeps mapping between machine config and test system
CREATE TABLE public.machine_system_mapping
(
    machine_id integer NOT NULL REFERENCES public.machineconfig(id),
    system_id integer NOT NULL REFERENCES public.test_systems(id),
    UNIQUE(machine_id, system_id)
)
ALTER TABLE public.machine_system_mapping OWNER to backend;
GRANT ALL ON TABLE public.machine_system_mapping TO backend;
GRANT ALL ON TABLE public.machine_system_mapping TO backend_readonly;

-- Machine System Mapping Table. This just keeps mapping between machine config and test system
CREATE TABLE public.test_machine_mapping
(
    test_id integer NOT NULL REFERENCES public.tests(id),
    machine_id integer NOT NULL,
    machine_pool_id integer REFERENCES public.machine_pools(id),
    UNIQUE(test_id, machine_id, machine_pool_id)
)
ALTER TABLE public.test_machine_mapping OWNER to backend;
GRANT ALL ON TABLE public.test_machine_mapping TO backend;
GRANT ALL ON TABLE public.test_machine_mapping TO backend_readonly;

