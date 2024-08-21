from dataclasses import dataclass, field

from tato._node import OrderedNode
from tato._node_type import NodeType
from tato.index.index import Index


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

    index: Index
    topo_sorted_calls: list[OrderedNode]

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
                section._functions = sorted(
                    section._functions, key=lambda n: self.topo_sorted_calls.index(n)
                )


def categorize_sections(
    topo_sorted_called_by: list[OrderedNode],
    index: Index,
    topo_sorted_calls: list[OrderedNode],
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
    builder = SectionsBuilder(index, topo_sorted_calls)

    for node in topo_sorted_called_by:
        builder.add(node)
    builder.seal()

    return builder.module_docstring + builder.imports, builder.sections
