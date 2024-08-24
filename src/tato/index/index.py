from pathlib import Path
from typing import MutableMapping

from libcst.codemod import CodemodContext, parallel_exec_transform_with_prettyprint
from libcst.metadata import FullRepoManager

from tato._debug import measure_time
from tato.index._collector import collect_files
from tato.index._controller import find_defdef, get_all_definitions
from tato.index._db import DB
from tato.index._definition import DefinitionCollector, ReferenceCollector
from tato.index._types import Definition


class Index:
    index_path: Path

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.db = DB(index_path)
        self._has_index = self.db.path.exists() and self.db.path.stat().st_size > 0

    def count_references(self, fully_qualified_name: str) -> int:
        """Counts all external references for a fully_qualified_name.

        What counts as an external reference?
            Usages in a different file from the original definition count as external references.
            Aliased usages in a different file count as external references.
            Imports do NOT count as references.
            References in the same file as the original definition do NOT count as external references.
        """
        if not self._has_index:
            return 0
        res = self.db.cursor.execute(
            """
            WITH RECURSIVE all_definitions(id, original_file_id) AS (
                -- Start with the original definition
                SELECT id, file_id FROM Definition WHERE Definition.fully_qualified_name = ?
                
                UNION ALL
                
                -- Recursively add all definitions that import this definition
                SELECT dd.to_definition_id, ad.original_file_id
                FROM DefDef dd
                JOIN all_definitions ad ON dd.from_definition_id = ad.id
            )
            SELECT COUNT(DISTINCT r.id) as reference_count
            FROM all_definitions ad
            JOIN DefRef dr ON dr.definition_id = ad.id
            JOIN Reference r ON r.id = dr.reference_id
            WHERE r.file_id != ad.original_file_id;
            """,
            (fully_qualified_name,),
        )
        return res.fetchone()[0]

    def create(self) -> None:
        with measure_time("Creating index..."):
            self.db.init_schema()

        package = self.index_path.parent
        manager = FullRepoManager(
            str(package.parent),
            paths=[str(p) for p in package.rglob("*.py")],
            providers=(
                set(DefinitionCollector.get_inherited_dependencies())
                | set(ReferenceCollector.get_inherited_dependencies())
            ),
        )
        context = CodemodContext(metadata_manager=manager)
        context.scratch["index_path"] = self.index_path

        files = collect_files(manager, package)
        self.db.bulk_insert(files)

        filemap = {f.path: f for f in files}

        transform = DefinitionCollector(context, files=filemap)
        parallel_exec_transform_with_prettyprint(
            transform, manager._paths, repo_root=str(manager.root_path)
        )

        definitions = get_all_definitions(self.db)
        defmap: MutableMapping[str, list[Definition]] = {}
        for d in definitions:
            if d not in defmap:
                defmap[d.fully_qualified_name] = [d]
            else:
                defmap[d.fully_qualified_name].append(d)

        defdefs = find_defdef(self.db)
        self.db.bulk_insert(defdefs)

        transform = ReferenceCollector(context, files=filemap, definitions=defmap)
        parallel_exec_transform_with_prettyprint(
            transform, manager._paths, repo_root=str(manager.root_path)
        )

        self._has_index = True


class NoopIndex(Index):
    def __init__(self, package: Path):
        self.index_path = package

    def count_references(self, fully_qualified_name: str) -> int:
        return 0

    def create(self, package: Path) -> None:
        return
