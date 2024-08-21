from pathlib import Path

from tato.index._collector import collect_definitions_and_references
from tato.index._db import DB


class Index:
    package: Path

    def __init__(self, package: Path):
        self.package = package
        self.db = DB(package.joinpath("tato.sqlite3"))
        self._has_index = self.db.path.exists() and self.db.path.stat().st_size > 0

    def count_references(self, fully_qualified_name: str) -> int:
        """Counts all references for a fully_qualified_name.

        What counts as a reference?
          Original definitions count as a reference.
          Usages count as references.
          Aliased usages count as references.
          Imports do NOT count as references.
        """
        if not self._has_index:
            return 0
        res = self.db.cursor.execute(
            """
            WITH RECURSIVE all_definitions(id) AS (
                -- Start with the original definition
                SELECT id FROM Definition WHERE Definition.fully_qualified_name = ?
                
                UNION ALL
                
                -- Recursively add all definitions that import this definition
                SELECT dd.to_definition_id
                FROM DefDef dd
                JOIN all_definitions ad ON dd.from_definition_id = ad.id
            )
            SELECT COUNT(DISTINCT r.id) as reference_count
            FROM all_definitions ad
            JOIN DefRef dr ON dr.definition_id = ad.id
            JOIN Reference r ON r.id = dr.reference_id;        
        """,
            (fully_qualified_name,),
        )
        return res.fetchone()[0]

    def create(self) -> None:
        self.db.init_schema()
        defs, refs, defrefs, defdefs = collect_definitions_and_references(self.package)
        self.db.bulk_insert(defs + refs + defrefs + defdefs)
        self._has_index = True


class NoopIndex(Index):
    def __init__(self, package: Path):
        self.package = package

    def count_references(self, fully_qualified_name: str) -> int:
        return 0

    def create(self, package: Path) -> None:
        return
