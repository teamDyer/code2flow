-- This file sets up various table used for ops and team management.
-- These tables add metatdata and other information to tests, teams, ops, and bugs.

-- Store a set of teams.
CREATE TABLE public.teams (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    UNIQUE(name)
);
ALTER TABLE public.teams OWNER to backend;
GRANT ALL ON TABLE public.teams TO backend;
GRANT SELECT ON TABLE public.teams TO backend_readonly;

-- Map keywords to teams for bug tracking
CREATE TABLE public.nvbugs_keywords (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    teamid integer NOT NULL REFERENCES public.teams(id),
    UNIQUE(name)
);
ALTER TABLE public.nvbugs_keywords OWNER to backend;
GRANT ALL ON TABLE public.nvbugs_keywords TO backend;
GRANT SELECT ON TABLE public.nvbugs_keywords TO backend_readonly;

-- Who owns ops?
CREATE TABLE public.ops_owner (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    email text NOT NULL,
    teamid integer NOT NULL REFERENCES public.teams(id)
);
ALTER TABLE public.ops_owner OWNER to backend;
GRANT ALL ON TABLE public.ops_owner TO backend;
GRANT SELECT ON TABLE public.ops_owner TO backend_readonly;

-- Who is relevant to ops?
CREATE TABLE public.ops_group (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    teamid integer NOT NULL REFERENCES public.teams(id)
);
ALTER TABLE public.ops_group OWNER to backend;
GRANT ALL ON TABLE public.ops_group TO backend;
GRANT SELECT ON TABLE public.ops_group TO backend_readonly;

-- Ops - data for day-to-day operations for an engineer to do their jobs.
CREATE TABLE public.ops (
    id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    wiki text NOT NULL,
    ownerid integer NOT NULL REFERENCES public.ops_owner(id),
    opsgroupid integer NOT NULL REFERENCES public.ops_group(id)
);
ALTER TABLE public.ops OWNER to backend;
GRANT ALL ON TABLE public.ops TO backend;
GRANT SELECT ON TABLE public.ops TO backend_readonly;

-- Bugs Table. This will hold all the bugs that the user want to track
CREATE TABLE public.bugs (
    id integer NOT NULL,
    team_id integer NOT NULL REFERENCES public.teams(id),
    platform text NOT NULL DEFAULT 'nvbugs',
    PRIMARY KEY(id, team_id, platform)
);
ALTER TABLE public.bugs OWNER to backend;
GRANT ALL ON TABLE public.bugs TO backend;
GRANT SELECT ON TABLE public.bugs TO backend_readonly;