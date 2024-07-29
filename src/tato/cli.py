import sys

import libcst.tool


def main():
    libcst.tool.main(
        "tato",
        ["codemod", "-x", "tato.tato.ReorderFileCodemod"] + sys.argv[1:],
    )
