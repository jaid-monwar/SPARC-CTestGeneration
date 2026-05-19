"""Graph operations - Python port of graph-ops.ts"""
import networkx as nx
from typing import Callable, Optional, List, Tuple, Dict, Set
from collections import deque

from .cfg_defs import CFG, GraphNode, merge_node_attrs


def distance_from_entry(cfg: CFG) -> Dict[str, int]:
    """Calculate BFS distance from entry node"""
    levels = {}
    queue = deque([(cfg.entry, 0)])
    visited = set()

    while queue:
        node, depth = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        levels[node] = depth

        for successor in cfg.graph.successors(node):
            if successor not in visited:
                queue.append((successor, depth + 1))

    return levels


def simplify_cfg(cfg: CFG, merge_attrs: Optional[Callable[[GraphNode, GraphNode], Optional[GraphNode]]] = None) -> CFG:
    """
    Simplify the CFG by removing trivial nodes.

    Two linked nodes are considered trivial if:
    - The source only has one outgoing edge
    - The destination only has one incoming edge
    """
    graph = cfg.graph.copy()

    # Find nodes to collapse
    to_collapse: List[Tuple[str, str]] = []
    for source, target in graph.edges():
        if graph.out_degree(source) == 1 and graph.in_degree(target) == 1:
            to_collapse.append((source, target))

    # Sort by topological order
    levels = distance_from_entry(cfg)
    to_collapse.sort(key=lambda pair: levels.get(pair[0], 0))

    entry = cfg.entry

    try:
        for source, target in to_collapse:
            if source not in graph.nodes() or target not in graph.nodes():
                continue

            # Try to merge node attributes
            if merge_attrs:
                node_attrs = graph.nodes[source]
                into_attrs = graph.nodes[target]

                # Convert to GraphNode objects
                source_node = GraphNode(**node_attrs)
                target_node = GraphNode(**into_attrs)

                merged_attrs = merge_attrs(source_node, target_node)
                if merged_attrs is None:
                    continue

                # Update target node with merged attributes
                for key, value in merged_attrs.__dict__.items():
                    graph.nodes[target][key] = value

            # Redirect all edges from source to target
            for edge_source, _, edge_key, edge_data in list(graph.in_edges(source, keys=True, data=True)):
                if edge_source != target:
                    graph.add_edge(edge_source, target, key=edge_key, **edge_data)

            for _, edge_target, edge_key, edge_data in list(graph.out_edges(source, keys=True, data=True)):
                if edge_target != source:
                    graph.add_edge(target, edge_target, key=edge_key, **edge_data)

            # Remove source node
            graph.remove_node(source)

            # Update entry if needed
            if entry == source:
                entry = target

    except Exception as e:
        print(f"Error during simplification: {e}")

    return CFG(
        entry=entry,
        graph=graph,
        offset_to_node=cfg.offset_to_node.clone()
    )


def trim_for(cfg: CFG) -> CFG:
    """
    Remove all nodes not reachable from the CFG's entry.

    Args:
        cfg: The CFG to trim

    Returns:
        A copy of the CFG with unreachable nodes removed
    """
    # Find all reachable nodes using BFS
    reachable: Set[str] = set()
    queue = deque([cfg.entry])

    while queue:
        node = queue.popleft()
        if node in reachable:
            continue
        reachable.add(node)

        for successor in cfg.graph.successors(node):
            if successor not in reachable:
                queue.append(successor)

    # Create subgraph with only reachable nodes
    trimmed_graph = cfg.graph.subgraph(reachable).copy()

    return CFG(
        entry=cfg.entry,
        graph=trimmed_graph,
        offset_to_node=cfg.offset_to_node.clone()
    )


def detect_backlinks(graph: nx.MultiDiGraph, entry: str) -> List[Dict[str, str]]:
    """
    Detect back edges (cycles) in the graph.

    Args:
        graph: The graph to analyze
        entry: The entry node

    Returns:
        List of backlink dictionaries with 'from' and 'to' keys
    """
    backlinks: List[Dict[str, str]] = []
    stack: List[Tuple[str, Set[str]]] = [(entry, set())]
    visited: Set[str] = set()

    def already_found(backlink: Dict[str, str]) -> bool:
        return any(
            item['from'] == backlink['from'] and item['to'] == backlink['to']
            for item in backlinks
        )

    while stack:
        node, path = stack.pop()
        if node in visited:
            continue
        visited.add(node)

        for child in graph.successors(node):
            # Check for cycles (including self-loops)
            if child in path or child == node:
                backlink = {'from': node, 'to': child}
                if not already_found(backlink):
                    backlinks.append(backlink)
                continue

            # Add child to stack with updated path
            new_path = path.copy()
            new_path.add(node)
            stack.append((child, new_path))

    return backlinks
