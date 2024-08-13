import libcst as cst
from libcst import codemod
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from tato._graph import create_graphs, topological_sort
from tato._section import categorize_sections


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
    )

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        graphs = create_graphs(original_node, self.metadata)
        topo_sorted = topological_sort(graphs["called_by"])
        imports, sections = categorize_sections(topo_sorted)

        return updated_node.with_changes(
            body=[i.node for i in imports]
            + [n.node for s in sections for n in s.flatten()]
        )
