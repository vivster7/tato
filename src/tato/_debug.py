import libcst as cst


def _debug_source_code(node: cst.CSTNode) -> str:
    """Return source code. Useful for debugging."""
    tree = cst.parse_module("")
    tree = tree.with_changes(body=[node])
    return tree.code
