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


def create_graph(
    module: cst.Module, metadata: Mapping[ProviderT, Mapping[cst.CSTNode, object]]
) -> dict[cst.CSTNode, set[cst.CSTNode]]:
    """Create a graph of definitions."""
    scopes = cast(Mapping[cst.CSTNode, Scope], metadata[ScopeProvider]).values()
    parents = cast(Mapping[cst.CSTNode, cst.CSTNode], metadata[ParentNodeProvider])

    def find_parent(node: cst.CSTNode) -> cst.CSTNode:
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
            # Using first global assignment. This seems likely to be buggy.
            globalassignment = next(
                (
                    a
                    for a in access.referents
                    if a.scope == globalscope and isinstance(a, Assignment)
                ),
                None,
            )
            if not globalassignment:
                # Skip non-global assignments.
                continue

            graph[find_parent(globalassignment.node)].add(find_parent(access.node))

    # sort the values
    indexes = {node: i for i, node in enumerate(module.body)}
    for key in graph:
        graph[key] = set(sorted(graph[key], key=lambda node: indexes[node]))

    return graph


def topological_sort(graph: dict[cst.CSTNode, set[cst.CSTNode]]) -> list[cst.CSTNode]:
    """
    Sorts a graph of definitions into a topological order.

    Example:
    >>> topological_sort({'a': {'b'}, 'b': {'c'}, 'c': set(), 'd': set()})
    ['d', 'c', 'b', 'a']
    """

    def sort_fn(node: cst.CSTNode) -> int:
        if isinstance(node, cst.SimpleStatementLine):
            if isinstance(node.body[0], (cst.Assign, cst.AnnAssign, cst.AugAssign)):
                return 1
            elif isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
                return 0
            else:
                return 2  # Unknown
        elif isinstance(node, (cst.ClassDef,)):
            return 3
        elif isinstance(node, (cst.FunctionDef,)):
            return 4
        else:
            return 2  # Unknown

    topo_sorted = []
    innodes: defaultdict[CSTNode, int] = defaultdict(int)
    for src, dsts in graph.items():
        innodes[src]
        for dst in dsts:
            innodes[dst] += 1

    queue = deque([node for node, count in innodes.items() if count == 0])
    while queue:
        # Sorting ensures we see constants/unknowns before classes and functions.
        # This allows to use the end of constants/unkwns as a section end.
        queue = deque(sorted(queue, key=sort_fn))
        node = queue.popleft()
        topo_sorted.append(node)
        for dst in graph[node]:
            innodes[dst] -= 1
            if innodes[dst] == 0:
                queue.append(dst)

    return topo_sorted


def categorize(node: cst.CSTNode):
    if isinstance(node, cst.SimpleStatementLine):
        if isinstance(node.body[0], (cst.Assign, cst.AnnAssign, cst.AugAssign)):
            return "constants"
        elif isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
            return "imports"
        else:
            return "unknown"
    elif isinstance(node, (cst.ClassDef,)):
        return "classes"
    elif isinstance(node, (cst.FunctionDef,)):
        return "functions"
    else:
        return "unknown"


def categorize_nodes(
    topo_sorted: list[cst.CSTNode],
) -> tuple[list[cst.SimpleStatementLine], list[list[cst.CSTNode]]]:
    """Categorize into: imports + sections.

    A section is:
     - constants
     - unknonws
     - classes
     - functions

    After we see a constant or unknown, we collect the following
    consecutive constants/unknowns, then start a new section.
    """
    imports, sections = [], []
    constants, unknowns, classes, functions = [], [], [], []

    i = 0
    while i < len(topo_sorted):
        node = topo_sorted[i]
        category = categorize(node)

        if category == "imports":
            imports.append(node)
        elif category == "constants" or category == "unknown":
            sections.extend(constants + unknowns + classes + functions)
            constants, unknowns, classes, functions = [], [], [], []

            if category == "constants":
                constants.append(node)
            elif category == "unknown":
                unknowns.append(node)

        elif category == "classes":
            classes.append(node)
        elif category == "functions":
            functions.append(node)
        else:
            raise Exception(f"Unknown category: {category}")

        i += 1

    if constants or unknowns or classes or functions:
        sections.extend(constants + unknowns + classes + functions)

    return imports, sections


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
        imports, sections = categorize_nodes(topo_sorted)

        return updated_node.with_changes(body=imports + sections)
