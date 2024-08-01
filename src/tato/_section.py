from dataclasses import dataclass, field
from xmlrpc.client import boolean

from tato._node import NodeType, OrderedNode


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
            # TODO: Check node.leaf_order
            self._functions.insert(0, node)
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

    imports: list[OrderedNode] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)

    _largest_node_type: NodeType = field(default=NodeType.IMPORT)
    _current: Section = field(default_factory=Section)
    _sealed: boolean = field(default=False)

    def add(self, node: OrderedNode) -> None:
        if self._sealed:
            raise ValueError("Cannot add to a sealed builder")
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
            self._sealed = True
