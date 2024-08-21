import argparse
from pathlib import Path
from typing import Optional

import libcst as cst
from libcst import codemod
from libcst.metadata import (
    FullyQualifiedNameProvider,
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from tato._graph import create_graphs, topological_sort
from tato._section import categorize_sections
from tato.index.index import Index, NoopIndex


class ReorderFileCodemod(codemod.VisitorBasedCodemodCommand):
    """Reorder files based on their internal file dependencies.

    Generally, it tries to order files by:
        1. Imports
        2. Constants/Expressions
        3. Classes (leaf classes first)
        4. Functions (leaf functions last)

    Occasionally, due to Python semantics, we'll have to break this order.
    In that case, we'll organize the file into sections, where each section
    is ordered.
    """

    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
        PositionProvider,
        FullyQualifiedNameProvider,
    )

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        arg_parser.add_argument(
            "--with-index",
            dest="with_index",
            metavar="INDEX",
            help="Path to index file",
            type=str,
        )

    def __init__(
        self, context: codemod.CodemodContext, index_path: Optional[str] = None
    ) -> None:
        super().__init__(context)
        self.index = Index(Path(index_path)) if index_path else NoopIndex(Path("."))

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        graphs = create_graphs(original_node, self.metadata, self.index)
        topo_sorted_called_by = topological_sort(graphs["called_by"])
        topo_sorted_calls = topological_sort(graphs["calls"])
        imports, sections = categorize_sections(
            topo_sorted_called_by, self.index, topo_sorted_calls
        )

        return updated_node.with_changes(
            body=[i.node for i in imports]
            + [n.node for s in sections for n in s.flatten()]
        )
