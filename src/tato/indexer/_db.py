import dataclasses
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

from tato.indexer._types import Definition, DefRef, File, Reference


class DB:
    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def init_schema(self):
        schema = Path(__file__).parent / "db-schema.sql"
        self.cursor.executescript(schema.read_text())

    def bulk_insert(
        self, objects: Sequence[Union[File, Definition, Reference, DefRef]]
    ) -> None:
        # Disable foreign key constraints for the duration of the transaction
        self.cursor.execute("PRAGMA foreign_keys = OFF")

        try:
            self.conn.execute("BEGIN TRANSACTION")

            for obj in objects:
                table_name = type(obj).__name__
                data = dataclasses.asdict(obj)
                columns = ", ".join(data.keys())
                placeholders = ", ".join("?" * len(data))
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                self.cursor.execute(query, tuple(data.values()))

            # Re-enable foreign key constraints before committing
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            # Ensure foreign key constraints are re-enabled even if an exception occurs
            self.cursor.execute("PRAGMA foreign_keys = ON")

    def bulk_delete(
        self, delete_specs: List[Tuple[type, List[Tuple[str, str, Any]]]]
    ) -> None:
        # Disable foreign key constraints for the duration of the transaction
        self.cursor.execute("PRAGMA foreign_keys = OFF")

        try:
            self.conn.execute("BEGIN TRANSACTION")

            for cls, conditions in delete_specs:
                table_name = cls.__name__
                if conditions:
                    where_clause = " AND ".join(
                        [f"{cond[0]} {cond[1]} ?" for cond in conditions]
                    )
                    query = f"DELETE FROM {table_name} WHERE {where_clause}"
                    self.cursor.execute(query, tuple(cond[2] for cond in conditions))
                else:
                    # If no conditions are provided, delete all records from the table
                    query = f"DELETE FROM {table_name}"
                    self.cursor.execute(query)

            # Re-enable foreign key constraints before committing
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            # Ensure foreign key constraints are re-enabled even if an exception occurs
            self.cursor.execute("PRAGMA foreign_keys = ON")

    def select(
        self, cls: type, conditions: Optional[List[Tuple[str, str, Any]]] = None
    ) -> List[Any]:
        table_name = cls.__name__
        query = f"SELECT * FROM {table_name}"
        if conditions:
            where_clause = " AND ".join(
                [f"{cond[0]} {cond[1]} ?" for cond in conditions]
            )
            query += f" WHERE {where_clause}"

        if conditions:
            self.cursor.execute(query, tuple(cond[2] for cond in conditions))
        else:
            self.cursor.execute(query)

        rows = self.cursor.fetchall()
        return [
            cls(**{f.name: row[f.name] for f in dataclasses.fields(cls)})
            for row in rows
        ]

    def close(self):
        self.conn.close()
