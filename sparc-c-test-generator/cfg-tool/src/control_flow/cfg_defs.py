"""CFG type definitions and data structures - Python port of cfg-defs.ts"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Callable
from enum import Enum
import networkx as nx


class NodeType(str, Enum):
    """Types of nodes in the CFG"""
    YIELD = "YIELD"
    THROW = "THROW"
    MARKER_COMMENT = "MARKER_COMMENT"
    LOOP_HEAD = "LOOP_HEAD"
    LOOP_EXIT = "LOOP_EXIT"
    SELECT = "SELECT"
    SELECT_MERGE = "SELECT_MERGE"
    COMMUNICATION_CASE = "COMMUNICATION_CASE"
    TYPE_CASE = "TYPE_CASE"
    TYPE_SWITCH_MERGE = "TYPE_SWITCH_MERGE"
    TYPE_SWITCH_VALUE = "TYPE_SWITCH_VALUE"
    GOTO = "GOTO"
    LABEL = "LABEL"
    CONTINUE = "CONTINUE"
    BREAK = "BREAK"
    START = "START"
    END = "END"
    CONDITION = "CONDITION"
    ASSERT_CONDITION = "ASSERT_CONDITION"
    STATEMENT = "STATEMENT"
    RETURN = "RETURN"
    EMPTY = "EMPTY"
    MERGE = "MERGE"
    FOR_INIT = "FOR_INIT"
    FOR_CONDITION = "FOR_CONDITION"
    FOR_UPDATE = "FOR_UPDATE"
    FOR_EXIT = "FOR_EXIT"
    SWITCH_CONDITION = "SWITCH_CONDITION"
    SWITCH_MERGE = "SWITCH_MERGE"
    CASE_CONDITION = "CASE_CONDITION"
    EXIT_PROCESS = "EXIT_PROCESS"


class EdgeType(str, Enum):
    """Types of edges in the CFG"""
    REGULAR = "regular"
    CONSEQUENCE = "consequence"
    ALTERNATIVE = "alternative"
    EXCEPTION = "exception"


class ClusterType(str, Enum):
    """Types of clusters in the CFG"""
    WITH = "with"
    TRY = "try"
    EXCEPT = "except"
    ELSE = "else"
    FINALLY = "finally"
    TRY_COMPLEX = "tryComplex"


@dataclass
class Cluster:
    """Represents a cluster (grouping) of nodes in the CFG"""
    id: int
    type: ClusterType
    parent: Optional['Cluster'] = None
    depth: int = 0


@dataclass
class GraphNode:
    """Attributes of a node in the CFG"""
    type: NodeType
    code: str
    lines: int = 1
    markers: List[str] = field(default_factory=list)
    cluster: Optional[Cluster] = None
    targets: List[str] = field(default_factory=list)
    start_offset: int = 0


@dataclass
class GraphEdge:
    """Attributes of an edge in the CFG"""
    type: EdgeType = EdgeType.REGULAR


@dataclass
class Goto:
    """Represents a goto statement"""
    label: str
    node: str


@dataclass
class ExitStatement:
    """Represents a break or continue statement"""
    from_node: str
    label: Optional[str] = None


@dataclass
class BasicBlock:
    """
    Represents a basic block in the CFG during construction.

    A BasicBlock can span many CFG nodes and represents a "statement"
    or "block" of source code.
    """
    entry: str
    exit: Optional[str] = None
    continues: List[ExitStatement] = field(default_factory=list)
    breaks: List[ExitStatement] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    gotos: List[Goto] = field(default_factory=list)
    function_exits: List[str] = field(default_factory=list)


class BlockHandler:
    """Handles break, continue, goto, and label statements during CFG construction"""

    def __init__(self):
        self.breaks: List[ExitStatement] = []
        self.continues: List[ExitStatement] = []
        self.labels: Dict[str, str] = {}
        self.gotos: List[Goto] = []
        self.function_exits: List[str] = []

    def _should_handle(self, label: Optional[str]) -> Callable[[ExitStatement], bool]:
        """Create a predicate to check if a statement should be handled"""
        def predicate(stmt: ExitStatement) -> bool:
            if not stmt.label:
                return True
            return stmt.label == label
        return predicate

    def for_each_break(self, callback: Callable[[str], None], label: Optional[str] = None) -> None:
        """Process all collected breaks and clear them"""
        predicate = self._should_handle(label)
        matching_breaks = [b for b in self.breaks if predicate(b)]
        self.breaks = [b for b in self.breaks if not predicate(b)]

        for break_stmt in matching_breaks:
            callback(break_stmt.from_node)

    def for_each_continue(self, callback: Callable[[str], None], label: Optional[str] = None) -> None:
        """Process all collected continues and clear them"""
        predicate = self._should_handle(label)
        matching_continues = [c for c in self.continues if predicate(c)]
        self.continues = [c for c in self.continues if not predicate(c)]

        for continue_stmt in matching_continues:
            callback(continue_stmt.from_node)

    def for_each_function_exit(self, callback: Callable[[str], str]) -> None:
        """Process all function exits"""
        self.function_exits = [callback(exit_node) for exit_node in self.function_exits]

    def process_gotos(self, callback: Callable[[str, str], None]) -> None:
        """Process all goto statements"""
        for goto in self.gotos:
            label_node = self.labels.get(goto.label)
            if label_node:
                callback(goto.node, label_node)

    def update(self, block: BasicBlock) -> BasicBlock:
        """Update the handler state with a new block and return updated block"""
        self.breaks.extend(block.breaks)
        self.continues.extend(block.continues)
        self.gotos.extend(block.gotos)
        self.function_exits.extend(block.function_exits)
        self.labels.update(block.labels)

        return BasicBlock(
            entry=block.entry,
            exit=block.exit,
            breaks=self.breaks.copy(),
            continues=self.continues.copy(),
            gotos=self.gotos.copy(),
            labels=self.labels.copy(),
            function_exits=self.function_exits.copy()
        )


@dataclass
class CFG:
    """The complete CFG structure"""
    graph: nx.MultiDiGraph
    entry: str
    offset_to_node: 'Lookup[str]'  # type: ignore # Will be defined in ranges module


@dataclass
class BuilderOptions:
    """Options for building the CFG"""
    flat_switch: bool = True
    marker_pattern: Optional[str] = None
    call_processor: Optional[Callable] = None


def merge_node_attrs(from_node: GraphNode, into_node: GraphNode) -> Optional[GraphNode]:
    """
    Merge attributes of two nodes, or return None to abort merge.

    Args:
        from_node: The node to disappear
        into_node: The node accepting the new attributes

    Returns:
        New node attributes if merge is successful, None to abort
    """
    if from_node.cluster != into_node.cluster:
        return None

    no_merge_types = {NodeType.YIELD, NodeType.THROW, NodeType.EXIT_PROCESS}
    if from_node.type in no_merge_types or into_node.type in no_merge_types:
        return None

    start_offset = min(from_node.start_offset, into_node.start_offset)

    return GraphNode(
        type=from_node.type,
        code=f"{from_node.code}\n{into_node.code}",
        lines=from_node.lines + into_node.lines,
        markers=from_node.markers + into_node.markers,
        cluster=from_node.cluster,
        targets=from_node.targets + into_node.targets,
        start_offset=start_offset
    )


def get_node_remapper(cfg: CFG) -> Callable[[str], str]:
    """Create a function that remaps node IDs based on their targets"""
    remap = {}
    for node_id in cfg.graph.nodes():
        node_attrs = cfg.graph.nodes[node_id]
        for target in node_attrs['targets']:
            remap[target] = node_id

    return lambda node: remap.get(node, node)


def remap_node_targets(cfg: CFG) -> CFG:
    """
    Remap node targets after simplification.

    Args:
        cfg: The CFG to remap

    Returns:
        CFG with remapped node targets
    """
    remapper = get_node_remapper(cfg)
    offset_to_node = cfg.offset_to_node.map_values(remapper)

    # Copy the graph
    graph = cfg.graph.copy()

    return CFG(
        entry=cfg.entry,
        graph=graph,
        offset_to_node=offset_to_node
    )


# Import Lookup here to avoid circular imports
from ..utils.ranges import Lookup
CFG.__annotations__['offset_to_node'] = Lookup[str]
