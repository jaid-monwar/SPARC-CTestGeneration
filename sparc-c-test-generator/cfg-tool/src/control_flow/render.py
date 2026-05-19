"""DOT rendering - Python port of theme.ts and render.ts"""
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import networkx as nx

from .cfg_defs import CFG, NodeType, EdgeType, ClusterType, Cluster
from .colors import ColorScheme, get_default_color_scheme
from .graph_ops import detect_backlinks


# Node style classes
NODE_CLASSES = {'default', 'entry', 'exit', 'yield', 'throw', 'terminate'}
EDGE_CLASSES = {'consequence', 'alternative', 'regular', 'exception'}
CLUSTER_CLASSES = {'with', 'try', 'except', 'finally', 'tryComplex'}


def get_node_style(node_class: str, color_scheme: ColorScheme) -> Dict[str, str]:
    """Get DOT attributes for a node class"""
    styles = {
        'default': {'shape': 'box', 'style': 'filled', 'class': 'default'},
        'entry': {'shape': 'invhouse', 'class': 'entry'},
        'exit': {'shape': 'house', 'class': 'exit'},
        'throw': {'shape': 'triangle', 'class': 'throw'},
        'yield': {'shape': 'hexagon', 'orientation': '90', 'class': 'yield'},
        'terminate': {'shape': 'doublecircle', 'class': 'terminate'},
    }

    dot_attrs = styles.get(node_class, styles['default']).copy()
    dot_attrs['fillcolor'] = color_scheme.get(f'node.{node_class}', '#d3d3d3')
    dot_attrs['color'] = color_scheme.get('node.border', '#000000')
    return dot_attrs


def get_node_height(node_class: str, lines: int) -> float:
    """Calculate node height based on lines of code"""
    min_height = 0.5 if node_class in ('entry', 'exit') else 0.3
    return max(lines * 0.3, min_height)


def get_edge_default_style(color_scheme: ColorScheme) -> Dict[str, str]:
    """Get default edge style"""
    return {
        'penwidth': '1',
        'color': color_scheme.get('edge.regular', '#0000ff'),
        'headport': 'n',
        'tailport': 's'
    }


def get_edge_style(edge_class: str, is_backlink: bool, color_scheme: ColorScheme) -> Dict[str, str]:
    """Get DOT attributes for an edge"""
    dot_attrs = {}

    if edge_class == 'consequence':
        dot_attrs['class'] = 'consequence'
        dot_attrs['color'] = color_scheme.get('edge.consequence', '#008000')
    elif edge_class == 'alternative':
        dot_attrs['class'] = 'alternative'
        dot_attrs['color'] = color_scheme.get('edge.alternative', '#ff0000')
    elif edge_class == 'regular':
        dot_attrs['class'] = 'regular'
        dot_attrs['color'] = color_scheme.get('edge.regular', '#0000ff')
    elif edge_class == 'exception':
        dot_attrs['style'] = 'invis'
        dot_attrs['headport'] = 'e'
        dot_attrs['tailport'] = 'w'
    else:
        dot_attrs['color'] = 'fuchsia'

    if is_backlink:
        dot_attrs['penwidth'] = '2'
        dot_attrs['dir'] = 'back'
        dot_attrs['headport'] = 's'
        dot_attrs['tailport'] = 'n'

    return dot_attrs


def get_cluster_style(cluster_class: str, is_self_nested: bool, color_scheme: ColorScheme) -> Dict[str, str]:
    """Get DOT attributes for a cluster"""
    return {
        'penwidth': '6' if is_self_nested else '0',
        'class': cluster_class,
        'color': color_scheme.get('cluster.border', '#ffffff'),
        'bgcolor': color_scheme.get(f'cluster.{cluster_class}', '#ffffff')
    }


def format_style(style: Dict[str, str]) -> str:
    """Format style dictionary as DOT attribute string"""
    parts = []
    for name, value in style.items():
        if isinstance(value, (int, float)):
            parts.append(f'{name}={value}')
        elif isinstance(value, str):
            parts.append(f'{name}="{value}"')
    return '; '.join(parts)


def is_exit(graph: nx.MultiDiGraph, node: str) -> bool:
    """Check if a node is an exit node"""
    if graph.out_degree(node) == 0:
        return True

    # Exception edges don't count
    for _, _, data in graph.out_edges(node, data=True):
        if data.get('type') != EdgeType.EXCEPTION:
            return False
    return True


@dataclass
class Hierarchy:
    """Hierarchical cluster structure"""
    graph: nx.MultiDiGraph
    children: Dict[int, 'Hierarchy']
    cluster: Optional[Cluster] = None


def get_parents(cluster: Cluster) -> List[Cluster]:
    """Get all parent clusters in order"""
    parents = []
    current = cluster
    while current.parent:
        current = current.parent
        parents.append(current)
    return list(reversed(parents))


def build_hierarchy(cfg: CFG) -> Hierarchy:
    """Build cluster hierarchy from CFG"""
    hierarchy = Hierarchy(graph=cfg.graph.copy(), children={})

    # Collect nodes by cluster
    cluster_nodes: Dict[Cluster, List[str]] = {}
    for node_id in cfg.graph.nodes():
        node_attrs = cfg.graph.nodes[node_id]
        cluster = node_attrs.get('cluster')
        if cluster:
            if cluster not in cluster_nodes:
                cluster_nodes[cluster] = []
            cluster_nodes[cluster].append(node_id)

    # Sort clusters by depth
    sorted_clusters = sorted(cluster_nodes.items(), key=lambda x: x[0].depth)

    for cluster, nodes in sorted_clusters:
        current_parent = hierarchy
        for parent in get_parents(cluster):
            if parent.id not in current_parent.children:
                current_parent.children[parent.id] = Hierarchy(
                    graph=nx.MultiDiGraph(),
                    children={},
                    cluster=parent
                )
            current_parent = current_parent.children[parent.id]

        # Extract subgraph
        inner_graph = cfg.graph.subgraph(nodes).copy()
        outer_graph = hierarchy.graph.copy()

        # Remove inner edges from outer
        for u, v in inner_graph.edges():
            if outer_graph.has_edge(u, v):
                outer_graph.remove_edge(u, v)

        hierarchy.graph = outer_graph
        current_parent.children[cluster.id] = Hierarchy(
            graph=inner_graph,
            children={},
            cluster=cluster
        )

    return hierarchy


def render_node(top_graph: nx.MultiDiGraph, node: str, verbose: bool, color_scheme: ColorScheme) -> str:
    """Render a single node in DOT format"""
    node_attrs = top_graph.nodes[node]
    node_type = node_attrs.get('type', NodeType.STATEMENT)

    # Determine node class
    if node_type == NodeType.THROW:
        node_class = 'throw'
    elif node_type == NodeType.YIELD:
        node_class = 'yield'
    elif node_type == NodeType.EXIT_PROCESS:
        node_class = 'terminate'
    elif top_graph.degree(node) == 0:
        node_class = 'default'
    elif top_graph.in_degree(node) == 0:
        node_class = 'entry'
    elif is_exit(top_graph, node):
        node_class = 'exit'
    else:
        node_class = 'default'

    dot_attrs = get_node_style(node_class, color_scheme)
    dot_attrs['height'] = str(get_node_height(node_class, node_attrs.get('lines', 1)))
    dot_attrs['id'] = node

    if verbose:
        code = node_attrs.get('code', '').replace('"', '\\"')
        # Get the string value of the enum
        node_type_str = node_type.value if hasattr(node_type, 'value') else str(node_type)
        label = f"{node_type_str}\\n{code}"
        cluster = node_attrs.get('cluster')
        if cluster:
            label = f"[{cluster.id}:{cluster.type}] {label}"
        dot_attrs['label'] = label

    return f'{node} [{format_style(dot_attrs)}];'


def render_edge(source: str, target: str, top_graph: nx.MultiDiGraph, backlinks: List[Dict], color_scheme: ColorScheme) -> str:
    """Render an edge in DOT format"""
    # Check if this is a backlink
    is_backlink = any(bl['from'] == source and bl['to'] == target for bl in backlinks)

    # Get edge data
    edge_data = top_graph.get_edge_data(source, target)
    if edge_data:
        # Get first edge if multiple
        edge_type = list(edge_data.values())[0].get('type', EdgeType.REGULAR)
    else:
        edge_type = EdgeType.REGULAR

    dot_attrs = get_edge_style(edge_type.value if hasattr(edge_type, 'value') else edge_type, is_backlink, color_scheme)

    # Flip for backlinks
    if is_backlink:
        source, target = target, source

    return f'{source} -> {target} [{format_style(dot_attrs)}];'


def render_subgraphs(hierarchy: Hierarchy, top_graph: nx.MultiDiGraph, verbose: bool, backlinks: List[Dict], color_scheme: ColorScheme, indent_level: int = 0) -> str:
    """Render subgraphs recursively"""
    indent = '    ' * indent_level
    parts = []

    cluster_id = hierarchy.cluster.id if hierarchy.cluster else 'toplevel'
    parts.append(f'{indent}subgraph cluster_{cluster_id} {{')

    # Add cluster style
    if hierarchy.cluster:
        is_self_nested = hierarchy.cluster.type == hierarchy.cluster.parent.type if hierarchy.cluster.parent else False
        cluster_style = get_cluster_style(hierarchy.cluster.type.value, is_self_nested, color_scheme)
        parts.append(f'{indent}    {format_style(cluster_style)};')

    # Render nodes
    for node in hierarchy.graph.nodes():
        parts.append(f'{indent}    {render_node(top_graph, node, verbose, color_scheme)}')

    # Render child subgraphs
    for child in hierarchy.children.values():
        parts.append(render_subgraphs(child, top_graph, verbose, backlinks, color_scheme, indent_level + 1))

    # Render edges
    for source, target in hierarchy.graph.edges():
        parts.append(f'{indent}    {render_edge(source, target, top_graph, backlinks, color_scheme)}')

    parts.append(f'{indent}}}')
    return '\n'.join(parts)


def graph_to_dot(cfg: CFG, verbose: bool = False, color_scheme: Optional[ColorScheme] = None) -> str:
    """
    Convert a CFG to DOT format.

    Args:
        cfg: The CFG to render
        verbose: Whether to include code content in nodes
        color_scheme: Color scheme to use (defaults to dark)

    Returns:
        DOT format string
    """
    if color_scheme is None:
        color_scheme = get_default_color_scheme()

    hierarchy = build_hierarchy(cfg)
    backlinks = detect_backlinks(cfg.graph, cfg.entry)

    parts = []
    default_node_attrs = get_node_style('default', color_scheme)

    parts.append('digraph "" {')
    parts.append(f'    node [{format_style(default_node_attrs)}];')
    parts.append(f'    edge [{format_style(get_edge_default_style(color_scheme))}];')
    parts.append(f'    bgcolor="{color_scheme.get("graph.background", "#ffffff")}";')
    parts.append('')

    # Render all subgraphs
    for child in hierarchy.children.values():
        parts.append(render_subgraphs(child, cfg.graph, verbose, backlinks, color_scheme, 1))

    # Render top-level nodes and edges
    for node in hierarchy.graph.nodes():
        parts.append(f'    {render_node(cfg.graph, node, verbose, color_scheme)}')

    for source, target in hierarchy.graph.edges():
        parts.append(f'    {render_edge(source, target, cfg.graph, backlinks, color_scheme)}')

    parts.append('}')
    return '\n'.join(parts)
