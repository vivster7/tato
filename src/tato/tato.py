import heapq
from collections import defaultdict
from typing import Mapping, cast

import libcst as cst
from libcst import codemod
from libcst.metadata import (
    Assignment,
    CodeRange,
    ParentNodeProvider,
    PositionProvider,
    ProviderT,
    Scope,
    ScopeProvider,
)

from tato._node import NodeType, OrderedNode, TopLevelNode
from tato._section import Section, SectionsBuilder

# Expected to be larger than any possible line number.
LARGE_NUM = 10_000_000


class ReorderFileCodemod(codemod.VisitorBasedCodemodCommand):
    """Reorder files based on their internal file dependencies.

    Generally, it tries to order files by:
        1. Imports
        2. Constants/Expressions
        3. Classes (leaf classes first)
        4. Functions (leaf functions last)

    Ocassionally, due to Python semantics, we'll have to break this order.
    In that case, we'll organize the file into sections, where each section
    is ordered.
    """

    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
        PositionProvider,
    )

    def should_allow_multiple_passes(self) -> bool:
        """
        Call transform repeatedly until the tree doesn't change between passes.

        `test_mashed_potato()` shows a case when this necessary.
        """
        return True

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        graph = create_graph(original_node, self.metadata)
        topo_sorted = topological_sort(graph)
        imports, sections = categorize_nodes(topo_sorted)

        return updated_node.with_changes(
            body=[i.node for i in imports]
            + [n.node for s in sections for n in s.flatten()]
        )


def create_graph(
    module: cst.Module, metadata: Mapping[ProviderT, Mapping[cst.CSTNode, object]]
) -> dict[OrderedNode, set[OrderedNode]]:
    """Create a graph of definitions (assignments)

    :: returns:
        A tuple of two dicts:
            - A graph mapping between nodes (where nodes are top-level
              objects in a module's body)
            - A mapping of definitions to their first access position.

    Example:
        ```
        1 def a():
        2     b()
        3     c()
        4
        5 def b():
        6     c()
        7
        8 def c(): pass
        ```
        will return a graph:
            `{'a': {'b', 'c'}, 'b': {'c'}, 'c': set()}`
        and first access mapping:
            `{a: (10_000_000, 10_000_000), b: (2, 4), c: (3, 4)}`

    """
    scopes = cast(Mapping[cst.CSTNode, Scope], metadata[ScopeProvider]).values()
    parents = cast(Mapping[cst.CSTNode, cst.CSTNode], metadata[ParentNodeProvider])
    positions = cast(Mapping[cst.CSTNode, CodeRange], metadata[PositionProvider])

    modulebodyset: set[TopLevelNode] = set(module.body)
    globalscope = next((s.globals for s in scopes if s is not None))

    def find_top_level_node(node: cst.CSTNode) -> TopLevelNode:
        """Find the `cst.Module.body` that contains the given node."""
        while node not in modulebodyset:
            node = parents[node]
        return cast(TopLevelNode, node)

    graph: dict[TopLevelNode, list[TopLevelNode]] = {}
    first_access: dict[TopLevelNode, tuple[int, int]] = defaultdict(
        lambda: (LARGE_NUM, LARGE_NUM)
    )
    for node in module.body:
        graph[node] = []

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
            # Skip non-global assignments.
            if not globalassignment:
                continue

            top_level_assignment = find_top_level_node(globalassignment.node)
            top_level_access = find_top_level_node(access.node)

            # Skip self-edges.
            if top_level_assignment == top_level_access:
                continue

            # Create edge from top_level_assignment to top_level_access
            graph[top_level_assignment].append(top_level_access)

            # Track first access of the assignment.
            coderange = positions[access.node]
            first_access[top_level_assignment] = min(
                first_access[top_level_assignment],
                (coderange.start.line, coderange.start.column),
            )

    indexes = {node: i for i, node in enumerate(module.body)}
    ordered_nodes = [
        OrderedNode.from_cst_node(node, first_access, indexes) for node in module.body
    ]
    lookup = {n.node: n for n in ordered_nodes}
    return {lookup[k]: set(lookup[v] for v in vs) for k, vs in graph.items()}


def topological_sort(
    graph: dict[OrderedNode, set[OrderedNode]],
) -> list[OrderedNode]:
    """
    Sorts a graph of definitions into a topological order.

    Example:
    >>> topological_sort({'a': {'b'}, 'b': {'c'}, 'c': set(), 'd': set()})
    ['d', 'c', 'b', 'a']
    """

    topo_sorted = []
    innodes: defaultdict[OrderedNode, int] = defaultdict(int)
    for src, dsts in graph.items():
        innodes[src]
        # Ignore usages of imports when sorting.
        if src.node_type == NodeType.IMPORT:
            continue
        for dst in dsts:
            innodes[dst] += 1

    # Using a heap (sorted list) ensures each section is ordered and each time
    # we see something out of order, we can start a new section.
    heap = [node for node, count in innodes.items() if count == 0]
    heapq.heapify(heap)
    while heap:
        node = heapq.heappop(heap)
        topo_sorted.append(node)
        for dst in graph[node]:
            innodes[dst] -= 1
            if innodes[dst] == 0:
                heapq.heappush(heap, dst)
    return topo_sorted


def categorize_nodes(
    topo_sorted: list[OrderedNode],
) -> tuple[list[OrderedNode], list[Section]]:
    """Categorize into: imports + sections.

    A section is:
     - constants
     - unknonws
     - classes
     - functions

    We start a new section when something is "out of order", so each section is
    ordered (constants, unknowns, classes, functions).
    """
    builder = SectionsBuilder()

    for node in topo_sorted:
        builder.add(node)
    builder.seal()

    return builder.imports, builder.sections


def _print_code(node: cst.CSTNode) -> None:
    """Print the code of a node. Used for debugging."""
    tree = cst.parse_module("")
    tree = tree.with_changes(body=[node])
    print(tree.code)
