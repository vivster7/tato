import libcst as cst


def _print_code(node: cst.CSTNode) -> None:
    """Print the code of a node. Used for debugging."""
    tree = cst.parse_module("")
    tree = tree.with_changes(body=[node])
    print(tree.code)
