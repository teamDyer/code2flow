--- A very simple "debug" test used for testing and experimentation.
CREATE TABLE vrl.simple (
    id serial NOT NULL PRIMARY KEY,
    original_id integer NOT NULL,
    payload text NOT NULL,
    UNIQUE(original_id)
);
ALTER TABLE vrl.simple OWNER to backend;
GRANT ALL ON TABLE vrl.simple TO backend;
GRANT SELECT ON TABLE vrl.simple TO backend_readonly;
-- Register test suite
INSERT INTO public.test_meta (system, name) VALUES ('vrl', 'simple');