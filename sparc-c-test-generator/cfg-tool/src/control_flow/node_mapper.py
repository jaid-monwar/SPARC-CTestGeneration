"""Node mapping utilities - Python port of node-mapper.ts"""
from tree_sitter import Node
from typing import Dict, List, Tuple, Optional
from ..utils.ranges import Lookup


class NodeMapper:
    """
    Maintains bidirectional mapping between:
    - Source code offsets ↔ AST nodes
    - AST nodes ↔ CFG nodes
    """

    def __init__(self):
        self.syntax_to_node: Dict[int, str] = {}  # Maps node.id to CFG node
        self.ranges: List[Tuple[int, int, Node]] = []  # (start, stop, syntax_node)

    def link_syntax_to_node(self, syntax: Node, node: str) -> None:
        """
        Link an AST syntax node to a CFG node.

        Args:
            syntax: The AST node
            node: The CFG node ID
        """
        self.syntax_to_node[syntax.id] = node
        self.ranges.append((syntax.start_byte, syntax.end_byte, syntax))

    def link_offset_to_syntax(
        self,
        from_node: Node,
        to_node: Node,
        reverse: bool = False,
        include_to: bool = False,
        include_from: bool = False
    ) -> None:
        """
        Link a range of offsets to a syntax node.

        Args:
            from_node: Start node
            to_node: End node
            reverse: If True, map to from_node instead of to_node
            include_to: If True, include to_node's end position
            include_from: If True, include from_node's start position
        """
        target = from_node if reverse else to_node
        to_index = to_node.end_byte if include_to else to_node.start_byte
        from_index = from_node.start_byte if include_from else from_node.end_byte

        self._add_range(from_index, to_index, target)

    def _add_range(self, start: int, stop: int, syntax: Node) -> None:
        """Add a range mapping"""
        self.ranges.append((start, stop, syntax))

    def _get_mapping(self) -> Dict[int, str]:
        """Get mapping from syntax IDs to node names"""
        return self.syntax_to_node.copy()

    def _build_ranges(self, function_syntax: Node) -> Lookup[Node]:
        """Build the range lookup structure"""
        lookup = Lookup(function_syntax)

        # Sort ranges from largest to smallest
        sorted_ranges = sorted(
            self.ranges,
            key=lambda r: r[1] - r[0],
            reverse=True
        )

        for start, stop, value in sorted_ranges:
            lookup.add(start, stop, value)

        return lookup

    def get_index_mapping(self, function_syntax: Node) -> Lookup[str]:
        """
        Get the final index to CFG node mapping.

        Args:
            function_syntax: The function's AST node

        Returns:
            Lookup structure mapping offsets to CFG node IDs
        """
        syntax_to_node = self._get_mapping()
        ranges = self._build_ranges(function_syntax)

        return ranges.map_values(
            lambda syntax: syntax_to_node.get(syntax.id, "Not found")
        )
