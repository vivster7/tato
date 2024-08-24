from pathlib import Path

from libcst.helpers import calculate_module_and_package
from libcst.metadata import FullRepoManager

from tato.index._types import File
from tato.lib.uuid import uuid7str


def collect_files(manager: FullRepoManager, package: Path) -> list[File]:
    files = []
    for path in package.rglob("*.py"):
        mod_pkg = calculate_module_and_package(manager.root_path, str(path))
        f = File(
            id=uuid7str(),
            path=path.relative_to(manager.root_path).as_posix(),
            module=mod_pkg.name,
            package=mod_pkg.package,
        )
        files.append(f)
    return files
