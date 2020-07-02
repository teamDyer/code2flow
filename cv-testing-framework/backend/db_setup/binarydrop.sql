-- DVS Build Packages
CREATE TABLE dvs.binarydrop(
    id SERIAL NOT NULL PRIMARY KEY,
    branch TEXT NOT NULL,
    build TEXT NOT NULL,
    shortname TEXT NOT NULL,
    name TEXT NOT NULL,
    scrape_periodically BOOLEAN NOT NULL,
    UNIQUE(name)
);
ALTER TABLE dvs.binarydrop OWNER to backend;
GRANT ALL ON TABLE dvs.binarydrop TO backend;
GRANT SELECT ON TABLE dvs.binarydrop TO backend_readonly;

-- DVS Changelists for packages
CREATE TABLE dvs.binarydrop_changelists(
    id SERIAL NOT NULL PRIMARY KEY,
    changelist TEXT NOT NULL,
    binarydrop_id integer REFERENCES dvs.binarydrop(id),
    url TEXT NOT NULL,
    UNIQUE(changelist, binarydrop_id)
);
ALTER TABLE dvs.binarydrop_changelists OWNER to backend;
GRANT ALL ON TABLE dvs.binarydrop_changelists TO backend;
GRANT SELECT ON TABLE dvs.binarydrop_changelists TO backend_readonly;

-- DVS Test Package Mapping
CREATE TABLE dvs.test_package_mapping(
    test_id integer NOT NULL REFERENCES public.tests(id),
    package_id integer NOT NULL REFERENCES dvs.binarydrop(id),
    UNIQUE(test_id, package_id)
);
ALTER TABLE dvs.test_package_mapping OWNER to backend;
GRANT ALL ON TABLE dvs.test_package_mapping TO backend;
GRANT SELECT ON TABLE dvs.test_package_mapping TO backend_readonly;
