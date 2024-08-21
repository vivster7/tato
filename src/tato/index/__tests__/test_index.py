from pathlib import Path

from tato.index.index import Index

PARENT = Path(__file__).parent


def test_index():
    package = PARENT.joinpath("data/index/test1")
    dbpath = package.joinpath("tato-index.sqlite3")
    if dbpath.exists():
        dbpath.unlink()

    index = Index(dbpath)

    assert index.count_references("does.not.exist") == 0

    index.create()

    assert index.count_references("does.not.exist") == 0
    assert index.count_references("test1.a.one") == 2
    assert index.count_references("test1.b.one") == 1
    assert index.count_references("test1.b.two") == 1
    assert index.count_references("test1.c.three") == 0
