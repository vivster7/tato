from collections import defaultdict
from functools import cache
from pathlib import Path

import libcst as cst
from libcst.metadata import (
    FullRepoManager,
    FullyQualifiedNameProvider,
)
from tato.index._collector import _create_context
from tato.index._definition import (
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


def test_definition_collector():
    root_path = PARENT.joinpath("data/definition/test1")
    filename = root_path.joinpath("a.py")
    context = _create_context(DefinitionCollector, create_manager(root_path), filename)

    defcollector = DefinitionCollector(context)
    wrapper = cst.ensure_type(context.wrapper, cst.MetadataWrapper)
    wrapper.visit(defcollector)

    # Check that the collector found the definition
    definitions = defcollector.definitions
    print([d.fully_qualified_name for d in definitions])
    assert len(definitions) == 6
    [d0, d1, d2, d3, d4, d5] = definitions

    assert d0.fully_qualified_name == "test1.a.defg"
    assert d1.fully_qualified_name == "test1.a.a"
    assert d2.fully_qualified_name == "test1.a.B"
    assert d3.fully_qualified_name == "test1.a.C"
    assert d4.fully_qualified_name == "test1.a.D"
    assert d5.fully_qualified_name == "test1.a.D"


def test_reference_colllector():
    root_path = PARENT.joinpath("data/definition/test2")

    alldefs = []
    for p in root_path.rglob("*.py"):
        context = _create_context(DefinitionCollector, create_manager(root_path), p)
        wrapper = cst.ensure_type(context.wrapper, cst.MetadataWrapper)
        defcollector = DefinitionCollector(context)
        wrapper.visit(defcollector)
        alldefs.extend(defcollector.definitions)

    definitions = defaultdict(list)
    for d in alldefs:
        definitions[d.fully_qualified_name].append(d)

    refcollector = ReferenceCollector(context, definitions=definitions)
    context = _create_context(ReferenceCollector, create_manager(root_path), p)
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
