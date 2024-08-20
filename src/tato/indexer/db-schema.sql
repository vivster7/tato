-- Create the File table
CREATE TABLE File (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    module TEXT NOT NULL,
    package TEXT NOT NULL
);

-- Create the Definition table
CREATE TABLE Definition (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    fully_qualified_name TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    start_col INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES File(id)
);

-- Create the Reference table
CREATE TABLE Reference (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    fully_qualified_name TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    start_col INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES File(id)
);

-- Create the DefRef table
CREATE TABLE DefRef (
    id TEXT PRIMARY KEY,
    definition_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    FOREIGN KEY (definition_id) REFERENCES Definition(id),
    FOREIGN KEY (reference_id) REFERENCES Reference(id)
);

-- Create indexes for better query performance
CREATE INDEX idx_file_path ON File(path);
CREATE INDEX idx_definition_file_id ON Definition(file_id);
CREATE INDEX idx_definition_fqn ON Definition(fully_qualified_name);
CREATE INDEX idx_reference_file_id ON Reference(file_id);
CREATE INDEX idx_reference_fqn ON Reference(fully_qualified_name);
CREATE INDEX idx_defref_definition_id ON DefRef(definition_id);
CREATE INDEX idx_defref_reference_id ON DefRef(reference_id);