import libcst as cst
from libcst.codemod import CodemodContext

from tato.index._types import File
from tato.lib.uuid import uuid7str

files: dict[tuple[str, str, str], "File"] = {}


def get_or_create_file(context: CodemodContext):
    path = cst.ensure_type(context.filename, str)
    module = cst.ensure_type(context.full_module_name, str)
    package = cst.ensure_type(context.full_package_name, str)
    key = (path, module, package)
    if key not in files:
        file = File(
            id=uuid7str(),
            path=path,
            module=module,
            package=package,
        )
        files[key] = file
    return files[key]
