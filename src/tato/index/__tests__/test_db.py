from pathlib import Path
from tempfile import NamedTemporaryFile

from tato.index._db import DB
from tato.index._types import Definition, DefRef, File, Reference
from tato.lib.uuid import uuid7str


def test_db():
    with NamedTemporaryFile() as f:
        db_manager = DB(Path(f.name))
        db_manager.init_schema()

        # Prepare objects for bulk insert
        file1 = File(
            id=uuid7str(),
            path="/path/to/file1.py",
            module="module1",
            package="package1",
        )
        file2 = File(
            id=uuid7str(),
            path="/path/to/file2.py",
            module="module2",
            package="package2",
        )

        def1 = Definition(
            id=uuid7str(),
            file_id=file1.id,
            fully_qualified_name="module1.func1",
            start_line=1,
            start_col=1,
        )
        def2 = Definition(
            id=uuid7str(),
            file_id=file2.id,
            fully_qualified_name="module2.func1",
            start_line=1,
            start_col=1,
        )

        ref1 = Reference(
            id=uuid7str(),
            file_id=file1.id,
            fully_qualified_name="module2.func1",
            start_line=5,
            start_col=1,
        )
        ref2 = Reference(
            id=uuid7str(),
            file_id=file2.id,
            fully_qualified_name="module1.func1",
            start_line=10,
            start_col=1,
        )

        defref1 = DefRef(id=uuid7str(), definition_id=def1.id, reference_id=ref2.id)
        defref2 = DefRef(id=uuid7str(), definition_id=def2.id, reference_id=ref1.id)

        # Perform bulk insert
        db_manager.bulk_insert([file1, file2, def1, def2, ref1, ref2, defref1, defref2])

        # Verify inserted data
        files = db_manager.select(File)
        definitions = db_manager.select(Definition)
        references = db_manager.select(Reference)
        defrefs = db_manager.select(DefRef)

        assert len(files) == 2
        assert len(definitions) == 2
        assert len(references) == 2
        assert len(defrefs) == 2

        # Perform bulk delete
        delete_specs = [
            (File, [("path", "LIKE", "%file1%")]),
            (Definition, [("fully_qualified_name", "=", "module2.func1")]),
            (Reference, []),  # This will delete all references
            (DefRef, [("definition_id", "=", def1.id)]),
        ]
        db_manager.bulk_delete(delete_specs)

        # Verify deleted data
        files = db_manager.select(File)
        definitions = db_manager.select(Definition)
        references = db_manager.select(Reference)
        defrefs = db_manager.select(DefRef)

        assert len(files) == 1
        assert len(definitions) == 1
        assert len(references) == 0
        assert len(defrefs) == 1

        db_manager.close()
