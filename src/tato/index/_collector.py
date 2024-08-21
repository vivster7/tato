from collections import defaultdict
from pathlib import Path
from typing import DefaultDict

from libcst import MetadataDependent
from libcst.codemod import CodemodContext
from libcst.helpers import calculate_module_and_package
from libcst.metadata import FullRepoManager, FullyQualifiedNameProvider

from tato.index._definition import (
    DefinitionCollector,
    ReferenceCollector,
)
from tato.index._types import DefDef, Definition, DefRef, Reference
from tato.lib.uuid import uuid7str


def collect_definitions_and_references(
    package: Path,
) -> tuple[list[Definition], list[Reference], list[DefRef], list[DefDef]]:
    root_path = package.parent
    manager = FullRepoManager(
        str(root_path),
        paths=[str(p) for p in package.rglob("*.py")],
        providers={FullyQualifiedNameProvider},
    )

    definitions, partial_defdefs = _collect_definitions(manager, package)

    definitions_map = defaultdict(list)
    for d in definitions:
        definitions_map[d.fully_qualified_name].append(d)

    defdefs = [
        DefDef(id=uuid7str(), from_definition_id=f.id, to_definition_id=t.id)
        for a, b in partial_defdefs
        for f in definitions_map[a]
        for t in definitions_map[b]
    ]

    references, defrefs = _collect_references(manager, package, definitions_map)
    return definitions, references, defrefs, defdefs


def _collect_definitions(
    manager: FullRepoManager,
    package_path: Path,
) -> tuple[list[Definition], list[tuple[str, str]]]:
    alldefs = []
    all_partial_defdefs = []
    for p in package_path.rglob("*.py"):
        context = _create_context(DefinitionCollector, manager, p)
        assert context.wrapper, "Wrapper should be set"

        defcollector = DefinitionCollector(context)
        context.wrapper.visit(defcollector)

        alldefs.extend(defcollector.definitions)
        all_partial_defdefs.extend(defcollector.partial_defdefs)

    return alldefs, all_partial_defdefs


def _collect_references(
    manager: FullRepoManager,
    package_path: Path,
    definitions_map: DefaultDict[str, list[Definition]],
) -> tuple[list[Reference], list[DefRef]]:
    allrefs = []
    alldefrefs = []
    for p in package_path.rglob("*.py"):
        context = _create_context(ReferenceCollector, manager, p)
        assert context.wrapper, "Wrapper should be set"

        refcollector = ReferenceCollector(
            context,
            definitions=definitions_map,
        )

        context.wrapper.visit(refcollector)

        allrefs.extend(refcollector.references)
        alldefrefs.extend(refcollector.defsrefs)

    return allrefs, alldefrefs


def _create_context(
    transform_cls: type[MetadataDependent], manager: FullRepoManager, path: Path
):
    wrapper = manager.get_metadata_wrapper_for_path(str(path))
    wrapper.resolve_many(transform_cls.METADATA_DEPENDENCIES)
    filename = path.relative_to(manager.root_path).as_posix()
    module_and_package = calculate_module_and_package(manager.root_path, path)
    return CodemodContext(
        filename=filename,
        full_module_name=module_and_package.name,
        full_package_name=module_and_package.package,
        wrapper=wrapper,
        metadata_manager=manager,
    )
