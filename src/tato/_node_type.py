import enum
from typing import Union

import libcst as cst
import libcst.matchers as m

# Type of a node found in a module's body.
TopLevelNode = Union[cst.SimpleStatementLine, cst.BaseCompoundStatement]


class NodeType(enum.IntEnum):
    IMPORT = 0
    CONSTANT = 1
    UNKNOWN = 2
    CLASS = 3
    FUNCTION = 4


def node_type(node: TopLevelNode) -> NodeType:
    if isinstance(node, cst.SimpleStatementLine):
        if isinstance(node.body[0], (cst.Assign, cst.AnnAssign, cst.AugAssign)):
            return NodeType.CONSTANT
        elif isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
            return NodeType.IMPORT
        else:
            return NodeType.UNKNOWN
    elif isinstance(node, (cst.ClassDef,)):
        return NodeType.CLASS
    elif isinstance(node, (cst.FunctionDef,)):
        return NodeType.FUNCTION
    else:
        # Treat `if TYPE_CHECKING:` blocks like imports
        if m.matches(node, m.If(test=m.Name("TYPE_CHECKING"))):
            return NodeType.IMPORT
        else:
            return NodeType.UNKNOWN
