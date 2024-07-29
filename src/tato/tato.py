from collections import defaultdict, deque
from typing import Iterable, Mapping, cast

import libcst as cst
from libcst import CSTNode, codemod
from libcst.metadata import (
    Assignment,
    ParentNodeProvider,
    ProviderT,
    Scope,
    ScopeProvider,
)

# TODO: REMOVE SELF EDGES


def create_graph(
    module: cst.Module, metadata: Mapping[ProviderT, Mapping[cst.CSTNode, object]]
) -> dict[cst.CSTNode, set[cst.CSTNode]]:
    """Create a graph of definitions."""
    scopes = cast(Mapping[cst.CSTNode, Scope], metadata[ScopeProvider]).values()
    parents = cast(Mapping[cst.CSTNode, cst.CSTNode], metadata[ParentNodeProvider])

    def find_parent_in_modulebody(node: cst.CSTNode) -> cst.CSTNode:
        """Find the `cst.Module.body` that contains the given node."""
        while node not in modulebody:
            node = parents[node]
        return node

    modulebody: Iterable[cst.CSTNode] = set(module.body)
    globalscope = next((s.globals for s in scopes if s is not None))

    graph: dict[cst.CSTNode, set[cst.CSTNode]] = {}
    for d in modulebody:
        graph[d] = set()

    for scope in scopes:
        if scope is None:
            continue
        for access in scope.accesses:
            if not any(r.scope == globalscope for r in access.referents):
                # Skip non-global references.
                continue

            assignment, *others = access.referents
            if others:
                raise ValueError(
                    f"Cannot handle multiple assignments, yet. {assignment.name}"
                )

            if assignment.scope == globalscope and isinstance(assignment, Assignment):
                graph[find_parent_in_modulebody(assignment.node)].add(
                    find_parent_in_modulebody(access.node)
                )
            else:
                # It's a local scope reference. Skip it.
                pass
    return graph


def topological_sort(graph: dict[cst.CSTNode, set[cst.CSTNode]]) -> list[cst.CSTNode]:
    """
    Sorts a graph of definitions into a topological order.

    Example:
    >>> topological_sort({'a': {'b'}, 'b': {'c'}, 'c': set(), 'd': set()})
    ['d', 'c', 'b', 'a']
    """
    topo_sorted = []
    innodes: defaultdict[CSTNode, int] = defaultdict(int)
    for src, dsts in graph.items():
        innodes[src]
        for dst in dsts:
            innodes[dst] += 1

    queue = deque([node for node, count in innodes.items() if count == 0])
    while queue:
        node = queue.popleft()
        topo_sorted.append(node)
        for dst in graph[node]:
            innodes[dst] -= 1
            if innodes[dst] == 0:
                queue.append(dst)

    return topo_sorted


def categorize_nodes(
    topo_sorted: list[cst.CSTNode],
) -> tuple[
    list[cst.SimpleStatementLine],
    list[cst.SimpleStatementLine],
    list[cst.ClassDef],
    list[cst.FunctionDef],
]:
    """Categorize into: imports, constants, classes, functions."""
    imports, constants, classes, functions = [], [], [], []

    for node in topo_sorted:
        if isinstance(node, cst.SimpleStatementLine):
            if isinstance(node.body[0], (cst.Assign, cst.AnnAssign, cst.AugAssign)):
                constants.append(node)
            elif isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
                imports.append(node)
            else:
                raise Exception(f"Unhandled node type: {node.body}")
        elif isinstance(node, (cst.ClassDef,)):
            classes.append(node)
        elif isinstance(node, (cst.FunctionDef,)):
            functions.append(node)
        else:
            raise Exception(f"Unhandled node type: {node}")

    return imports, constants, classes, functions


class ReorderFileCodemod(codemod.VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
    )

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        graph = create_graph(original_node, self.metadata)
        topo_sorted = topological_sort(graph)
        imports, constants, classes, functions = categorize_nodes(topo_sorted)

        return updated_node.with_changes(body=imports + constants + classes + functions)
