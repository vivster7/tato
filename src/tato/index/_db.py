import dataclasses
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

from tato.index._types import DefDef, Definition, DefRef, File, PartialDefDef, Reference


class DB:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def init_schema(self):
        schema = Path(__file__).parent / "db-schema.sql"
        self.cursor.executescript(schema.read_text())
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.conn.commit()

    def bulk_insert(
        self,
        objects: Sequence[
            Union[File, Definition, Reference, DefRef, DefDef, PartialDefDef]
        ],
    ) -> None:
        # Disable foreign key constraints
        self.cursor.execute("PRAGMA foreign_keys = OFF")

        batch_size = 5000
        total_inserted = 0

        try:
            for i in range(0, len(objects), batch_size):
                batch = objects[i : i + batch_size]

                self.conn.execute("BEGIN TRANSACTION")

                # Group objects by type
                grouped_objects = {}
                for obj in batch:
                    table_name = type(obj).__name__
                    if table_name not in grouped_objects:
                        grouped_objects[table_name] = []
                    grouped_objects[table_name].append(obj)

                # Insert each group
                for table_name, group in grouped_objects.items():
                    if not group:
                        continue

                    data = [dataclasses.asdict(obj) for obj in group]
                    columns = ", ".join(data[0].keys())
                    placeholders = ", ".join("?" * len(data[0]))
                    query = (
                        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    )

                    self.cursor.executemany(
                        query, [tuple(item.values()) for item in data]
                    )

                # Commit each batch
                self.conn.commit()
                total_inserted += len(batch)
                print(f"Inserted {total_inserted} objects")

        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            # Re-enable foreign key constraints
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
