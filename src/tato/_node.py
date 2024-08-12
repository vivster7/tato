from dataclasses import dataclass
from typing import Literal, Mapping

import libcst as cst

from tato._node_type import NodeType, TopLevelNode, node_type


@dataclass(frozen=True)
class OrderedNode:
    """Information needed to order TopLevelNodes."""

    node: TopLevelNode
    node_type: NodeType
    # The ealier a TopLevelNode is accessed, the earlier it should appear in the
    # output.
    # Acesss is the (lineno, colno) in the original file.
    first_access: tuple[int, int]
    # Tie break should be the order of the node in the original file.
    prev_body_index: int
    # 'leaf_last' allows for the most important / highest abstraction to be a
    #  the top of the file.
    # Due to Python semantics, most node_type's must be 'leaf_first', except
    # functions.
    leaf_order: Literal["leaf_first", "leaf_last"]
    _debug_source_code: str

    @classmethod
    def from_cst_node(
        cls,
        cstnode: TopLevelNode,
        first_access: Mapping[TopLevelNode, tuple[int, int]],
        indexes: Mapping[TopLevelNode, int],
    ):
        def leaf_type(node: TopLevelNode) -> Literal["leaf_first", "leaf_last"]:
            if isinstance(node, (cst.FunctionDef,)):
                return "leaf_last"
            else:
                return "leaf_first"

        def _debug_source_code(node: cst.CSTNode) -> str:
            """Print the code of a node. Used for debugging."""
            tree = cst.parse_module("")
            tree = tree.with_changes(body=[node])
            return tree.code

        return cls(
            node=cstnode,
            node_type=node_type(cstnode),
            first_access=first_access[cstnode],
            prev_body_index=indexes[cstnode],
            leaf_order=leaf_type(cstnode),
            _debug_source_code=_debug_source_code(cstnode),
        )

    def __hash__(self) -> int:
        return hash(self.node)

    def __eq__(self, other: "OrderedNode") -> bool:
        return self.node == other.node

    def __lt__(self, other: "OrderedNode") -> bool:
        return self._as_tuple() < other._as_tuple()

    def _as_tuple(self) -> tuple:
        if self.node_type == NodeType.IMPORT:
            # Try and keep imports sorted by their previous location.
            return (self.node_type, self.prev_body_index)
        else:
            if self.leaf_order == "leaf_first":
                return (self.node_type, self.first_access, self.prev_body_index)
            elif self.leaf_order == "leaf_last":
                # Err, I don't really understand why we have to multiply by -1.
                # Something about inserting functions in reverse order...
                return (
                    self.node_type,
                    self.first_access,
                    # (self.first_access[0] * -1, self.first_access[0] * -1),
                    # (self.first_access[0] * -1, self.first_access[0] * -1),
                    self.prev_body_index,
                )
            else:
                raise ValueError(f"Unknown leaf_order: {self.leaf_order}")
