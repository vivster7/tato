from collections import defaultdict, deque
from typing import Mapping, cast

import libcst as cst
from libcst import CSTNode, codemod
from libcst.metadata import (
    Assignment,
    CodeRange,
    ParentNodeProvider,
    PositionProvider,
    ProviderT,
    Scope,
    ScopeProvider,
)

# Expected to be larger than any possible line number.
LARGE_NUM = 10_000_000


class ReorderFileCodemod(codemod.VisitorBasedCodemodCommand):
    """Reorder files based on their internal file dependencies.

    Generally, it tries to order files by:
        1. Imports
        2. Constants/Expressions
        3. Classes (leaf classes first)
        4. Functions (leaf functions last)

    Somtimes constants may depend on classes/functions, so
    those are defined before constants.

    If there are multiple constants that depend on different
    functions/classes, we'll get multiple layers that look like:
        1. Imports
        2. Classes/Functions
        3. Constants/Expressions that use #2
        4. Classes/Functions
        5. Costants/Expressions that use #4
        ...
        8. Classes (leaf classes first)
        9. Functions (leaf functions last)

    This autoformatting will be far from perfect. Manually edits
    are encouraged. Or break up the file in to multiple files.
    """

    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
        PositionProvider,
    )

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        graph, first_access = create_graph(original_node, self.metadata)
        topo_sorted = topological_sort(graph, first_access)
        imports, sections = categorize_nodes(topo_sorted)

        return updated_node.with_changes(body=imports + sections)


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


def topological_sort(
    graph: dict[cst.CSTNode, set[cst.CSTNode]],
    first_access: dict[cst.CSTNode, tuple[int, int]],
) -> list[cst.CSTNode]:
    """
    Sorts a graph of definitions into a topological order.

    Example:
    >>> topological_sort({'a': {'b'}, 'b': {'c'}, 'c': set(), 'd': set()})
    ['d', 'c', 'b', 'a']
    """

    def sort_fn(node: cst.CSTNode) -> tuple[int, tuple[int, int]]:
        if isinstance(node, cst.SimpleStatementLine):
            if isinstance(node.body[0], (cst.Assign, cst.AnnAssign, cst.AugAssign)):
                return 1, first_access[node]
            elif isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
                return 0, first_access[node]
            else:
                return 2, first_access[node]  # Unknown
        elif isinstance(node, (cst.ClassDef,)):
            return 3, first_access[node]
        elif isinstance(node, (cst.FunctionDef,)):
            # Functions get sorted by leaf last. To order by access first after the 'reversal', we multiply by -1
            return (
                4,
                (first_access[node][0] * -1, first_access[node][1] * -1),
            )
        else:
            return 2, first_access[node]  # Unknown

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


def create_graph(
    module: cst.Module, metadata: Mapping[ProviderT, Mapping[cst.CSTNode, object]]
) -> tuple[dict[cst.CSTNode, set[cst.CSTNode]], dict[cst.CSTNode, tuple[int, int]]]:
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

    modulebodyset: set = set(module.body)
    globalscope = next((s.globals for s in scopes if s is not None))

    def find_parent(node: cst.CSTNode) -> cst.CSTNode:
        """Find the `cst.Module.body` that contains the given node."""
        while node not in modulebodyset:
            node = parents[node]
        return node

    graph: dict[cst.CSTNode, list[cst.CSTNode]] = {}
    first_access: dict[cst.CSTNode, tuple[int, int]] = defaultdict(
        lambda: (10_000_000, 10_000_000)
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
            if not globalassignment:
                # Skip non-global assignments.
                continue

            # Create edge from assignment parent to access parent.
            assignment_parent = find_parent(globalassignment.node)
            access_parent = find_parent(access.node)
            graph[assignment_parent].append(access_parent)

            # Track first access of the assignment.
            coderange = positions[access.node]
            first_access[assignment_parent] = min(
                first_access[assignment_parent],
                (coderange.start.line, coderange.start.column),
            )

    indexes = {node: i for i, node in enumerate(module.body)}
    return {
        key: set(sorted(values, key=lambda node: indexes[node]))
        for key, values in graph.items()
    }, first_access


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
            functions.insert(0, node)
        else:
            raise Exception(f"Unknown category: {category}")

        i += 1

    if constants or unknowns or classes or functions:
        sections.extend(constants + unknowns + classes + functions)

    return imports, sections
