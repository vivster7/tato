import sys

import libcst.tool
from libcst._version import __version__ as libcst_version

from tato.__about__ import __version__


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: tato [codemod] PATH [PATH ...]")
        return
    if sys.argv[1] in ("--version",):
        print(f"tato version {__version__} (libcst version {libcst_version})")
        return

    # The help text from libcst spits out 'usage: tato codemod' and exposes the
    # underlying libcst configuration. We can reuse that for now.
    args = sys.argv[1:]
    if sys.argv[1] == "codemod":
        args = sys.argv[2:]
    sys.exit(
        libcst.tool.main(
            "tato",
            ["codemod", "-x", "tato.tato.ReorderFileCodemod"] + args,
        )
    )
