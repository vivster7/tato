import argparse
import os
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
        self,
        context: codemod.CodemodContext,
        with_index: Optional[str] = None,
    ) -> None:
        super().__init__(context)
        self.with_index = with_index

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        # Connect to index (database) inside of the transform to avoid pickling
        # the db connections across forked processes.
        index = (
            Index(Path(self.with_index)) if self.with_index else NoopIndex(Path("."))
        )
        graphs = create_graphs(original_node, self.metadata, index)
        topo_sorted_called_by = topological_sort(graphs["called_by"])
        topo_sorted_calls = topological_sort(graphs["calls"])
        imports, sections = categorize_sections(
            topo_sorted_called_by, index, topo_sorted_calls
        )

        should_explain = os.environ.get("TATO_DEBUG_EXPLAIN", "") == "1"
        if should_explain:
            body = []
            body.append(_comment("## Section #1: Imports"))
            body.extend(i.node for i in imports)

            for i, section in enumerate(sections, start=2):
                body.append(_comment(f"## Section #{i}: Symbols, Classes, Functions"))
                for n in section.flatten():
                    commentbody = f"# {n.node_type}, Called by: {['|'.join(x.names) for x in graphs['called_by'][n]]}, Calls: {['|'.join(x.names) for x in graphs['calls'][n]]}, First access: {n.first_access if not n.has_cycle else 'cycle'}, Prev index: {n.prev_body_index}"
                    body.append(_comment(commentbody))
                    body.append(n.node)
        else:
            body = [i.node for i in imports] + [
                n.node for s in sections for n in s.flatten()
            ]

        return updated_node.with_changes(body=body)


def _comment(s: str) -> cst.EmptyLine:
    return cst.EmptyLine(comment=cst.Comment(s))
