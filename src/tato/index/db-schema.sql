-- Existing tables (unchanged)
CREATE TABLE File (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    module TEXT NOT NULL,
    package TEXT NOT NULL
);

CREATE TABLE Definition (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    fully_qualified_name TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    start_col INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES File(id)
);

CREATE TABLE Reference (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    fully_qualified_name TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    start_col INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES File(id)
);

CREATE TABLE DefRef (
    id TEXT PRIMARY KEY,
    definition_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    FOREIGN KEY (definition_id) REFERENCES Definition(id),
    FOREIGN KEY (reference_id) REFERENCES Reference(id)
);

-- New table for linking definitions
CREATE TABLE DefDef (
    id TEXT PRIMARY KEY,
    from_definition_id TEXT NOT NULL,
    to_definition_id TEXT NOT NULL,
    FOREIGN KEY (from_definition_id) REFERENCES Definition(id),
    FOREIGN KEY (to_definition_id) REFERENCES Definition(id)
);

CREATE TABLE PartialDefDef (
    from_qual_name TEXT NOT NULL,
    to_qual_name TEXT NOT NULL,
    PRIMARY KEY (from_qual_name, to_qual_name)
);


-- Indexes for better query performance
CREATE INDEX idx_file_path ON File(path);
CREATE INDEX idx_definition_file_id ON Definition(file_id);
CREATE INDEX idx_definition_fqn ON Definition(fully_qualified_name);
CREATE INDEX idx_reference_file_id ON Reference(file_id);
CREATE INDEX idx_reference_fqn ON Reference(fully_qualified_name);
CREATE INDEX idx_defref_definition_id ON DefRef(definition_id);
CREATE INDEX idx_defref_reference_id ON DefRef(reference_id);
CREATE INDEX idx_defdef_from ON DefDef(from_definition_id);
CREATE INDEX idx_defdef_to ON DefDef(to_definition_id);