import libcst as cst
from libcst.codemod import CodemodContext

from tato.index._types import File
from tato.lib.uuid import uuid7str

files: dict[tuple[str, str, str], "File"] = {}


def get_or_create_file(context: CodemodContext):
    path = cst.ensure_type(context.filename, str)
    module = cst.ensure_type(context.full_module_name, str)
    package = cst.ensure_type(context.full_package_name, str)
    return files.setdefault(
        (path, module, package), File(uuid7str(), path, module, package)
    )
