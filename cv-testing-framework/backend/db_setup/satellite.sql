--- Set up table for managing satellites.

-- Test meta table
CREATE TABLE public.satellite (
    id serial NOT NULL PRIMARY KEY,
    satellite_url TEXT NOT NULL,
    name TEXT NOT NULL,
    expires TIMESTAMPTZ NOT NULL,
    info JSONB NOT NULL,
    UNIQUE (satellite_url)
);
ALTER TABLE public.satellite OWNER to backend;
GRANT ALL ON TABLE public.satellite TO backend;
GRANT SELECT ON TABLE public.satellite TO backend_readonly;