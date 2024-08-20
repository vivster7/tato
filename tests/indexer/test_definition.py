from collections import defaultdict
from functools import cache
from pathlib import Path

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.helpers import calculate_module_and_package
from libcst.metadata import (
    FullRepoManager,
    FullyQualifiedNameProvider,
)
from tato.indexer._definition import (
    DefinitionCollector,
    ReferenceCollector,
)

PARENT = Path(__file__).parent


@cache
def create_manager(root_path: Path):
    return FullRepoManager(
        str(root_path.parent),
        paths=[str(p) for p in root_path.rglob("*.py")],
        providers={FullyQualifiedNameProvider},
    )


def create_context(root_path: Path, filepath: Path) -> CodemodContext:
    manager = create_manager(root_path)
    wrapper = manager.get_metadata_wrapper_for_path(str(filepath))
    wrapper.resolve_many(DefinitionCollector.METADATA_DEPENDENCIES)

    filename = filepath.relative_to(root_path).as_posix()
    module_and_package = calculate_module_and_package(root_path, filepath)

    return CodemodContext(
        filename=filename,
        full_module_name=module_and_package.name,
        full_package_name=module_and_package.package,
        wrapper=wrapper,
        metadata_manager=manager,
    )


def test_definition_collector():
    root_path = PARENT.joinpath("data/definition/test1")
    filename = root_path.joinpath("a.py")
    context = create_context(root_path, filename)

    defcollector = DefinitionCollector(context)
    wrapper = cst.ensure_type(context.wrapper, cst.MetadataWrapper)
    wrapper.visit(defcollector)

    # Check that the collector found the definition
    definitions = defcollector.definitions
    assert len(definitions) == 5
    [d1, d2, d3, d4, d5] = definitions

    assert d1.fully_qualified_name == "test1.a.a"
    assert d2.fully_qualified_name == "test1.a.B"
    assert d3.fully_qualified_name == "test1.a.C"
    assert d4.fully_qualified_name == "test1.a.D"
    assert d5.fully_qualified_name == "test1.a.D"


def test_reference_colllector():
    root_path = PARENT.joinpath("data/definition/test2")
    filename = root_path.joinpath("b.py")
    context = create_context(root_path, filename)

    defcollector = DefinitionCollector(context)
    for p in root_path.rglob("*.py"):
        context = create_context(root_path, p)
        wrapper = cst.ensure_type(context.wrapper, cst.MetadataWrapper)
        wrapper.visit(defcollector)

    definitions = defaultdict(list)
    for d in defcollector.definitions:
        definitions[d.fully_qualified_name].append(d)

    refcollector = ReferenceCollector(context, definitions=definitions)
    context = create_context(root_path, filename)
    wrapper = cst.ensure_type(context.wrapper, cst.MetadataWrapper)
    wrapper.visit(refcollector)

    assert len(refcollector.references) == 5
    [r1, r2, r3, r4, r5] = refcollector.references
    assert r1.fully_qualified_name == "test2.b.fn"
    assert r2.fully_qualified_name == "test2.a.a"
    assert r3.fully_qualified_name == "test2.a.B"
    assert r4.fully_qualified_name == "test2.a.C"
    assert r5.fully_qualified_name == "test2.a.D"

    # The 'test2.a.D' reference has two definitions
    assert len(refcollector.defsrefs) == 6
    assert len(definitions["test2.a.D"]) == 2
