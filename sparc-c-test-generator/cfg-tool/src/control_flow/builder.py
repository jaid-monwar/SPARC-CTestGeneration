"""Core CFG builder - Python port of builder.ts"""
import networkx as nx
from typing import Optional, Callable, TypeVar
from .cfg_defs import NodeType, EdgeType, GraphNode, GraphEdge, Cluster, ClusterType

T = TypeVar('T')


class Builder:
    """Constructs the CFG graph"""

    def __init__(self):
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.node_id = 0
        self.cluster_id = 0
        self.active_clusters: list[Cluster] = []

    def _start_cluster(self, cluster_type: ClusterType) -> Cluster:
        """Start a new cluster"""
        parent = self.active_clusters[-1] if self.active_clusters else None
        cluster = Cluster(
            id=self.cluster_id,
            type=cluster_type,
            parent=parent,
            depth=len(self.active_clusters) + 1
        )
        self.cluster_id += 1
        self.active_clusters.append(cluster)
        return cluster

    def _end_cluster(self, cluster: Cluster) -> None:
        """End a cluster (assumes stack-like behavior)"""
        self.active_clusters.pop()

    def with_cluster(self, cluster_type: ClusterType, fn: Callable[[Cluster], T]) -> T:
        """
        Execute a function within the context of a cluster.

        Args:
            cluster_type: The type of cluster to create
            fn: The function to execute within the cluster context

        Returns:
            The result of the function
        """
        cluster = self._start_cluster(cluster_type)
        try:
            return fn(cluster)
        finally:
            self._end_cluster(cluster)

    def add_node(self, node_type: NodeType, code: str, start_offset: int) -> str:
        """
        Add a node to the CFG.

        Args:
            node_type: Type of the node
            code: Source code text for the node
            start_offset: Offset in the source code

        Returns:
            The ID of the created node
        """
        node_id = f"node{self.node_id}"
        self.node_id += 1

        cluster = self.active_clusters[-1] if self.active_clusters else None

        self.graph.add_node(
            node_id,
            type=node_type,
            code=code,
            lines=1,
            markers=[],
            cluster=cluster,
            targets=[node_id],
            start_offset=start_offset
        )
        return node_id

    def clone_node(self, node: str, overrides: Optional[dict] = None) -> str:
        """
        Clone a node with optional attribute overrides.

        Args:
            node: The node ID to clone
            overrides: Optional dictionary of attributes to override

        Returns:
            The ID of the cloned node
        """
        node_id = f"node{self.node_id}"
        self.node_id += 1

        # Get original attributes
        original_attrs = self.graph.nodes[node].copy()

        # Preserve cluster reference (not deep copied)
        cluster = original_attrs.get('cluster')

        # Apply overrides if provided
        if overrides:
            original_attrs.update(overrides)
        else:
            original_attrs['cluster'] = cluster

        self.graph.add_node(node_id, **original_attrs)
        return node_id

    def add_marker(self, node: str, marker: str) -> None:
        """
        Add a marker to a node.

        Args:
            node: The node ID
            marker: The marker text
        """
        self.graph.nodes[node]['markers'].append(marker)

    def add_edge(self, source: str, target: str, edge_type: EdgeType = EdgeType.REGULAR) -> None:
        """
        Add an edge to the CFG.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Type of edge
        """
        # Check if edge already exists
        if self.graph.has_edge(source, target):
            return

        self.graph.add_edge(source, target, type=edge_type)

    def get_graph(self) -> nx.MultiDiGraph:
        """Return the current CFG graph"""
        return self.graph

    def set_default(self, node: str, defaults: dict) -> None:
        """
        Set default node attributes (only if not already set).

        Args:
            node: The node ID
            defaults: Dictionary of default attributes
        """
        node_attrs = self.graph.nodes[node]
        for key, value in defaults.items():
            if key not in node_attrs or node_attrs[key] is None:
                node_attrs[key] = value
