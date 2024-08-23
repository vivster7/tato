import libcst as cst
from libcst.codemod import ContextAwareTransformer
from libcst.helpers import (
    get_absolute_module_for_import_or_raise,
    get_full_name_for_node_or_raise,
)
from libcst.metadata import (
    Assignment,
    CodeRange,
    FullyQualifiedNameProvider,
    GlobalScope,
    PositionProvider,
    ScopeProvider,
)

from tato.index._controller import get_definitions, get_file
from tato.index._db import DB
from tato.index._types import Definition, DefRef, PartialDefDef, Reference
from tato.lib.uuid import uuid7str


class DefinitionCollector(ContextAwareTransformer):
    METADATA_DEPENDENCIES = (
        ScopeProvider,
        PositionProvider,
        FullyQualifiedNameProvider,
    )

    def visit_Module(self, node: cst.Module) -> bool:
        db = DB(self.context.scratch["index_path"])
        assert self.context.filename is not None
        f = get_file(db, self.context.filename)

        definitions: list[Definition] = []
        partial_defdefs: set[PartialDefDef] = set()

        global_scope = self.get_metadata(ScopeProvider, node)
        global_scope = cst.ensure_type(global_scope, GlobalScope)
        for assignment in global_scope.assignments:
            assignment = cst.ensure_type(assignment, Assignment)
            position = cst.ensure_type(
                self.get_metadata(PositionProvider, assignment.node), CodeRange
            )
            fqns = self.get_metadata(FullyQualifiedNameProvider, assignment.node, set())
            # Each assignment should only have 1 fqn
            assert len(fqns) <= 1, f"Expected 0 or 1 fqn, got {len(fqns)}"
            if fqns:
                [fqn] = fqns
                d = Definition(
                    id=uuid7str(),
                    file_id=f.id,
                    fully_qualified_name=fqn.name,
                    start_line=position.start.line,
                    start_col=position.start.column,
                )
                definitions.append(d)
            elif isinstance(assignment.node, cst.ImportFrom):
                if isinstance(assignment.node.names, cst.ImportStar):
                    # Skip import star references for now.
                    continue
                for name in assignment.node.names:
                    d = Definition(
                        id=uuid7str(),
                        file_id=f.id,
                        fully_qualified_name=f"{f.module}.{get_full_name_for_node_or_raise(name.name)}",
                        start_line=position.start.line,
                        start_col=position.start.column,
                    )
                    pd = PartialDefDef(
                        from_qual_name=f"{get_absolute_module_for_import_or_raise(f.module, assignment.node)}.{get_full_name_for_node_or_raise(name.name)}",
                        to_qual_name=d.fully_qualified_name,
                    )
                    definitions.append(d)
                    partial_defdefs.add(pd)
            elif isinstance(assignment.node, cst.Import):
                # TODO:
                pass

        db.bulk_insert(definitions)
        db.bulk_insert(list((partial_defdefs)))

        # I'm not sure why we need to reset these values. It's as if the same
        # instance is being used for multiple files...
        self.definitions = []
        self.defrefs = []

        return False


class ReferenceCollector(ContextAwareTransformer):
    METADATA_DEPENDENCIES = (
        ScopeProvider,
        PositionProvider,
        FullyQualifiedNameProvider,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.references: list[Reference] = []
        self.defrefs: list[DefRef] = []

    def visit_Attribute(self, node: cst.Attribute) -> bool:
        return self._visit_name_attr_alike(node)

    def visit_Name(self, node: cst.Name) -> bool:
        return self._visit_name_attr_alike(node)

    def _visit_name_attr_alike(self, node: cst.CSTNode) -> bool:
        db = DB(self.context.scratch["index_path"])
        assert self.context.filename is not None
        f = get_file(db, self.context.filename)

        found = False
        fqnames = self.get_metadata(FullyQualifiedNameProvider, node, set())

        for fqname in fqnames:
            if defs := get_definitions(db, fqname.name):
                found = True
                position = cst.ensure_type(
                    self.get_metadata(PositionProvider, node), CodeRange
                )
                r = Reference(
                    id=uuid7str(),
                    file_id=f.id,
                    fully_qualified_name=fqname.name,
                    start_line=position.start.line,
                    start_col=position.start.column,
                )
                self.references.append(r)
                for d in defs:
                    dr = DefRef(
                        id=uuid7str(),
                        definition_id=d.id,
                        reference_id=r.id,
                    )
                    self.defrefs.append(dr)

        # Optimization tos top recursing on children if we've found the reference.
        return not found

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        db = DB(self.context.scratch["index_path"])
        db.bulk_insert(self.references)
        db.bulk_insert(self.defrefs)
        # I'm not sure why we need to reset these values. It's as if the same
        # instance is being used for multiple files...
        self.references = []
        self.defrefs = []
        return updated_node
