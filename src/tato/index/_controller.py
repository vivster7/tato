from tato.index._db import DB
from tato.index._types import DefDef, Definition, File
from tato.lib.uuid import uuid7str


def get_file(db: DB, filename: str) -> File:
    res = db.cursor.execute("SELECT * FROM File WHERE path = ?", (filename,))
    return File(**res.fetchone())


def find_defdef(db: DB) -> list[DefDef]:
    sql = """
    SELECT d1.id as from_definition_id, d2.id as to_definition_id
    FROM PartialDefDef pdd
    JOIN Definition d1 ON d1.fully_qualified_name = pdd.from_qual_name
    JOIN Definition d2 ON d2.fully_qualified_name = pdd.to_qual_name
    """
    res = db.cursor.execute(sql)
    return [DefDef(id=uuid7str(), **row) for row in res.fetchall()]


def get_definitions(db: DB, fqname: str) -> list[Definition]:
    sql = """
    SELECT *
    FROM Definition 
    WHERE fully_qualified_name = ?
    """
    res = db.cursor.execute(sql, (fqname,))
    return [Definition(**row) for row in res.fetchall()]


def get_all_definitions(db: DB) -> list[Definition]:
    sql = """
    SELECT *
    FROM Definition
    """
    res = db.cursor.execute(sql)
    return [Definition(**row) for row in res.fetchall()]
