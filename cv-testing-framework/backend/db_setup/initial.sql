-- Sets up the intial, long lived tables for the compiler hub database on a fresh postgres
-- install. Should not mess up an existing compiler hub database if run against it.
-- Most of the table's here are for managing tests, as well as common tables for denormalized
-- data to reduce storage space.

-- Postgres hierarchy:
-- - cluser - one instance of runnig postgres is called a cluster.
-- - database - one cluster contains multiple databases - database don't share any data besides roles and users, which are scoped to the cluster.
-- - schemas - schemas contain other named objects. They are basically a form of namespaces.
-- - tables - finally we have concrete tables at this level. Other named things like views live here.

-- Create a couple of schemas
CREATE SCHEMA IF NOT EXISTS vrl;
CREATE SCHEMA IF NOT EXISTS dvs;

-- Main role used by the backend
CREATE USER backend WITH
    NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
    ENCRYPTED PASSWORD %(backend_password)s;
GRANT USAGE ON SCHEMA vrl TO backend;
GRANT USAGE ON SCHEMA dvs TO backend;

-- Readonly role used by the backend. Used for custom queries to prevent users
-- from doing damage with queries.
CREATE USER backend_readonly WITH
    NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
    ENCRYPTED PASSWORD %(backend_readonly_password)s;
GRANT USAGE ON SCHEMA vrl TO backend_readonly;
GRANT USAGE ON SCHEMA dvs TO backend_readonly;

-- Test meta table
CREATE TABLE public.test_meta (
    id serial NOT NULL PRIMARY KEY,
    system text NOT NULL,
    name text NOT NULL,
    CONSTRAINT testmeta_name_system_key UNIQUE (name, system)
);
ALTER TABLE public.test_meta OWNER to backend;
GRANT ALL ON TABLE public.test_meta TO backend;
GRANT SELECT ON TABLE public.test_meta TO backend_readonly;

-- Scrapers table - store all registered scraping jobs.
CREATE TABLE public.test_scrapers (
    id serial NOT NULL PRIMARY KEY,
    test_meta_id integer NOT NULL REFERENCES public.test_meta(id),
    scrape_tag text NOT NULL,
    scrape_params jsonb NOT NULL,
    enabled boolean NOT NULL,
    UNIQUE(test_meta_id, scrape_tag, scrape_params)
);
ALTER TABLE public.test_scrapers OWNER to backend;
GRANT ALL ON TABLE public.test_scrapers TO backend;
GRANT SELECT ON TABLE public.test_scrapers TO backend_readonly;

-- Visualizations - a combination of queries and parameters that can be used to store
-- useful queries for later use, such that a user need not manually configure the query again.
CREATE TABLE public.test_visualizations (
    id serial NOT NULL PRIMARY KEY,
    test_meta_id integer NOT NULL REFERENCES public.test_meta(id),
    query_name text NOT NULL,
    query_params jsonb NOT NULL,
    render_name text NOT NULL,
    renderer_params jsonb NOT NULL
);
ALTER TABLE public.test_visualizations OWNER to backend;
GRANT ALL ON TABLE public.test_visualizations TO backend;
GRANT SELECT ON TABLE public.test_visualizations TO backend_readonly;