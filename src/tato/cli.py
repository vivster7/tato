import argparse
import sys

import libcst.tool
from libcst._version import __version__ as libcst_version

from tato.__about__ import __version__


def main() -> None:
    parser = argparse.ArgumentParser(description="Tato CLI tool")
    parser.add_argument("codemod", nargs="?", help="Alias for tato command")
    parser.add_argument("paths", nargs="*", help="Paths to process")
    parser.add_argument("--package", nargs="?", help="Package to process")
    parser.add_argument(
        "--version",
        action="version",
        version=f"tato version {__version__} (libcst version {libcst_version})",
    )

    args = parser.parse_args()

    if not args.paths:
        parser.print_usage()
        return

    # The help text from libcst spits out 'usage: tato codemod' and exposes the
    # underlying libcst configuration. We can reuse that for now.
    libcst_args = ["codemod", "-x", "tato.tato.ReorderFileCodemod"]
    if args.package:
        libcst_args.extend(["--package", args.package])
    sys.exit(libcst.tool.main("tato", libcst_args + args.paths))
