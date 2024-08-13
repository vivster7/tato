import heapq
from collections import defaultdict
from typing import Mapping, TypedDict, cast

import libcst as cst
from libcst.metadata import (
    CodeRange,
    ParentNodeProvider,
    PositionProvider,
    ProviderT,
    Scope,
    ScopeProvider,
)

from tato._node import OrderedNode, TopLevelNode
from tato._node_type import NodeType, node_type

Graph = dict[OrderedNode, set[OrderedNode]]

# Expected to be larger than any possible line number.
LARGE_NUM = 10_000_000


class Graphs(TypedDict):
    calls: Graph
    called_by: Graph


def create_graphs(
    module: cst.Module, metadata: Mapping[ProviderT, Mapping[cst.CSTNode, object]]
) -> Graphs:
    """Create a graph of definitions (assignments)

    :: returns:
        A tuple of two graphs:
            1. The `calls` graph is used to topologically sort most nodes in a
               "deps-first" manner.
            2. The `called_by` graph is used to topologically sort
               the functions sections in a "deps-last" manner.

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
        would return:
            calls: `{'a': {'b', 'c'}, 'b': {'c'}, 'c': set()}`
            called_by: `{'a': {}, 'b': {'a'}, 'c': {'a', 'b'}}`


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

    calls: dict[TopLevelNode, list[TopLevelNode]] = {}
    called_by: dict[TopLevelNode, list[TopLevelNode]] = {}
    first_access: dict[TopLevelNode, tuple[int, int]] = defaultdict(
        lambda: (LARGE_NUM, LARGE_NUM)
    )
    for node in module.body:
        calls[node] = []
        called_by[node] = []

    globalscope = next((s.globals for s in scopes if s is not None), None)
    if globalscope is None:
        raise Exception("No global scope found")

    for assignment in globalscope.assignments:
        for access in assignment.references:
            top_level_assignment = find_top_level_node(assignment.node)
            top_level_access = find_top_level_node(access.node)

            # Skip self-edges.
            if top_level_assignment == top_level_access:
                continue

            # Ignore usages of imports
            if node_type(top_level_assignment) == NodeType.IMPORT:
                continue

            # Create edge from top_level_assignment to top_level_access
            if (
                node_type(top_level_assignment) == NodeType.FUNCTION
                and node_type(top_level_access) == NodeType.FUNCTION
                and access.scope == globalscope
            ):
                # This is.. super confusing. A decorator is called by the function it decorates (access).
                # But when topological sorting calls for functions, the decorator must be defined before the function.
                # In this case, the decorator "calls" the function. This needs a better / more clear concept.
                # I'm overloading
                calls[top_level_assignment].append(top_level_access)
                called_by[top_level_assignment].append(top_level_access)
            else:
                calls[top_level_access].append(top_level_assignment)
                called_by[top_level_assignment].append(top_level_access)

            # Skip any edges that cause cycles in the graph.
            if _has_cycles(calls) or _has_cycles(called_by):
                calls[top_level_access].pop()
                called_by[top_level_assignment].pop()
                continue

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
    return {
        "calls": {lookup[k]: set(lookup[v] for v in vs) for k, vs in calls.items()},
        "called_by": {
            lookup[k]: set(lookup[v] for v in vs) for k, vs in called_by.items()
        },
    }


def topological_sort(graph: Graph) -> list[OrderedNode]:
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


def _has_cycles(graph: dict[TopLevelNode, list[TopLevelNode]]) -> bool:
    """Returns true is the graph has cycles."""

    visited = set()
    stack = set()

    def dfs(node: TopLevelNode):
        if node in visited:
            return False
        if node in stack:
            return True
        stack.add(node)
        for dst in graph[node]:
            if dfs(dst):
                return True
        stack.remove(node)
        visited.add(node)
        return False

    for node in graph:
        if dfs(node):
            return True
    return False
