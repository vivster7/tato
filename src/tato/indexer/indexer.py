from functools import cache
from pathlib import Path

from tato.indexer._collector import collect_definitions_and_references
from tato.indexer._db import DB


def count_references(db: DB, fully_qualified_name: str) -> int:
    if not _has_index(db):
        return 0
    res = db.cursor.execute(
        """
        SELECT COUNT(*)
        FROM defref
        JOIN definition ON defref.definition_id = definition.id
        WHERE definition.fully_qualified_name = ?
    """,
        (fully_qualified_name,),
    )
    return res.fetchone()[0]


def create_index(db: DB, package: Path) -> None:
    db.init_schema()
    defs, refs, defrefs = collect_definitions_and_references(package)
    db.bulk_insert(defs + refs + defrefs)
    _has_index.cache_clear()


@cache
def _has_index(db: DB):
    return Path(db.path).exists() and Path(db.path).stat().st_size > 0
