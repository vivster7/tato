from dataclasses import dataclass, field

import libcst as cst
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from tato._graph import create_graphs, topological_sort
from tato._node import OrderedNode
from tato._node_type import NodeType


@dataclass
class Section:
    """Grouping of ordered nodes"""

    _constants: list[OrderedNode] = field(default_factory=list)
    _unknowns: list[OrderedNode] = field(default_factory=list)
    _classes: list[OrderedNode] = field(default_factory=list)
    _functions: list[OrderedNode] = field(default_factory=list)

    def add(self, node: OrderedNode) -> None:
        if node.node_type == NodeType.CONSTANT:
            self._constants.append(node)
        elif node.node_type == NodeType.UNKNOWN:
            self._unknowns.append(node)
        elif node.node_type == NodeType.CLASS:
            self._classes.append(node)
        elif node.node_type == NodeType.FUNCTION:
            self._functions.append(node)
        else:
            raise ValueError(f"Unknown node_type: {node.node_type}")

    def flatten(self) -> list[OrderedNode]:
        return self._constants + self._unknowns + self._classes + self._functions


@dataclass
class SectionsBuilder:
    """Construct the sections of the output.

    A new section if we've already seen a larger node_type in the current
    section.
    """

    module_docstring: list[OrderedNode] = field(default_factory=list)
    imports: list[OrderedNode] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)

    _largest_node_type: NodeType = field(default=NodeType.IMPORT)
    _current: Section = field(default_factory=Section)
    _sealed: bool = field(default=False)

    def add(self, node: OrderedNode) -> None:
        if self._sealed:
            raise ValueError("Cannot add to a sealed builder")
        if node.node_type == NodeType.MODULE_DOCSTRING:
            self.module_docstring.append(node)
            return
        if node.node_type == NodeType.IMPORT:
            self.imports.append(node)
            return
        if self._largest_node_type > node.node_type:
            self.sections.append(self._current)
            self._current = Section()
        self._current.add(node)
        self._largest_node_type = node.node_type

    def seal(self) -> None:
        if not self._sealed:
            self.sections.append(self._current)
            self.sort_functions_sections()
            self._sealed = True

    def sort_functions_sections(self) -> None:
        """Sort functions by call hierarchy order."""
        for section in self.sections:
            if section._functions:
                temp_module = cst.parse_module("")
                temp_module = temp_module.with_changes(
                    body=[n.node for n in section._functions]
                )
                wrapper = cst.MetadataWrapper(temp_module, unsafe_skip_copy=True)
                metadata = wrapper.resolve_many(
                    [
                        ScopeProvider,
                        ParentNodeProvider,
                        PositionProvider,
                    ]
                )
                graphs = create_graphs(temp_module, metadata)
                topo_nodes = topological_sort(graphs["calls"])
                section._functions = [n for n in topo_nodes]


def categorize_sections(
    topo_sorted: list[OrderedNode],
) -> tuple[list[OrderedNode], list[Section]]:
    """Categorize into: imports + sections.

    A section is:
     - constants
     - unknonws
     - classes
     - functions

    We start a new section when something is "out of order", so each section is
    ordered (constants, unknowns, classes, functions).

    Functions get resorted by call hierarchy order when sealed.
    """
    builder = SectionsBuilder()

    for node in topo_sorted:
        builder.add(node)
    builder.seal()

    return builder.module_docstring + builder.imports, builder.sections
