from pathlib import Path

from tato.indexer._db import DB
from tato.indexer.indexer import count_references, create_index

PARENT = Path(__file__).parent


def test_collector():
    package = PARENT.joinpath("data/indexer/test1")
    dbpath = package.joinpath("tato.sqlite3")
    if dbpath.exists():
        dbpath.unlink()
    db = DB(dbpath)
    assert count_references(db, "does.not.exist") == 0

    create_index(db, package)

    assert count_references(db, "does.not.exist") == 0
    assert count_references(db, "test1.a.one") == 2
    assert count_references(db, "test1.b.two") == 1
