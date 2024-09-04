import enum
from typing import Optional, Union

import libcst as cst
import libcst.matchers as m

# Type of a node found in a module's body.
TopLevelNode = Union[cst.SimpleStatementLine, cst.BaseCompoundStatement]


class NodeType(enum.IntEnum):
    MODULE_DOCSTRING = 0
    IMPORT = 1
    CONSTANT = 2
    UNKNOWN = 3
    CLASS = 4
    FUNCTION = 5

    def __str__(self) -> str:
        return self.name


def node_type(node: TopLevelNode, old_module_index: Optional[int] = None) -> NodeType:
    if isinstance(node, cst.SimpleStatementLine):
        if isinstance(node.body[0], (cst.Assign, cst.AnnAssign, cst.AugAssign)):
            return NodeType.CONSTANT
        elif isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
            return NodeType.IMPORT
        else:
            if old_module_index == 0 and isinstance(node.body[0], cst.Expr):
                return NodeType.MODULE_DOCSTRING
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
