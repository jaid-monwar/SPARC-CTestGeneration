"""Block matching utilities - Python port of block-matcher.ts"""
from tree_sitter import Node, Query
from typing import Optional, List, Callable, Dict
from .cfg_defs import BasicBlock, BlockHandler
from ..utils.evolve import evolve


def get_tree_language(syntax: Node):
    """
    Get the language from a syntax node.
    In Python tree-sitter, we need to walk up to find the tree.
    """
    # Walk up to root to get the tree
    node = syntax
    while node.parent is not None:
        node = node.parent
    # Root node's walk() gives us access to the tree indirectly
    # But we need to pass language when creating the query
    # So we'll need to store it in the BlockMatcher
    return None  # Placeholder - will be set in BlockMatcher


def match_exists_in(syntax: Node, query_string: str, language) -> bool:
    """
    Check if a query matches in the given syntax node.

    Args:
        syntax: The syntax node to query
        query_string: The tree-sitter query string
        language: The tree-sitter Language object

    Returns:
        True if matches exist, False otherwise
    """
    if not language:
        return False

    query = Query(language, query_string)
    matches = query.matches(syntax)
    return len(matches) > 0


class Match:
    """Utility class for matching against AST using queries"""

    def __init__(
        self,
        match_captures_dict: Dict[str, List[Node]],
        block_handler: BlockHandler,
        dispatch_single: Callable[[Node, Optional[dict]], BasicBlock]
    ):
        # Convert the captures dict to the format expected by the rest of the code
        self.captures_dict = match_captures_dict
        self.block_handler = block_handler
        self.dispatch_single = dispatch_single

    def get_syntax(self, name: str) -> Optional[Node]:
        """Get the first named syntax node from the query match"""
        nodes = self.get_syntax_many(name)
        return nodes[0] if nodes else None

    def get_last_syntax(self, name: str) -> Optional[Node]:
        """Get the last named syntax node from the query match"""
        nodes = self.get_syntax_many(name)
        return nodes[-1] if nodes else None

    def require_syntax(self, name: str) -> Node:
        """Get the first named syntax node, raising error if not found"""
        syntax = self.get_syntax(name)
        if syntax is None:
            raise ValueError(f"Failed getting syntax for {name}")
        return syntax

    def get_syntax_many(self, name: str) -> List[Node]:
        """Get all named syntax nodes from the query match"""
        return self.captures_dict.get(name, [])

    def get_block(self, syntax: Optional[Node]) -> Optional[BasicBlock]:
        """Get a basic block from a syntax node"""
        if syntax is None:
            return None
        return self.block_handler.update(self.dispatch_single(syntax, None))

    def get_many_blocks(self, syntax_many: List[Node]) -> List[BasicBlock]:
        """Get basic blocks from multiple syntax nodes"""
        return [self.get_block(syntax) for syntax in syntax_many if syntax is not None]


class BlockMatcher:
    """Manages block matching and state during CFG construction"""

    def __init__(self, dispatch_single: Callable[[Node, Optional[dict]], BasicBlock], language=None):
        self.block_handler = BlockHandler()
        self.dispatch_single = dispatch_single
        self.language = language

    def match(
        self,
        syntax: Node,
        query_string: str,
        options: Optional[Dict] = None
    ) -> Match:
        """
        Match a query against a syntax node.

        Args:
            syntax: The syntax node to match against
            query_string: The tree-sitter query string
            options: Optional query options

        Returns:
            A Match object containing the results
        """
        if not self.language:
            raise ValueError("BlockMatcher has no language set")

        query = Query(self.language, query_string)

        # Execute query and get first match
        matches = query.matches(syntax)

        if not matches:
            raise ValueError("No match found for query.")

        # Take the first match (pattern_index, captures_dict)
        pattern_idx, captures_dict = matches[0]

        return Match(captures_dict, self.block_handler, self.dispatch_single)

    def try_match(self, syntax: Node, query_string: str) -> Optional[Match]:
        """
        Try to match a query, returning None on failure.

        Args:
            syntax: The syntax node to match against
            query_string: The tree-sitter query string

        Returns:
            A Match object if successful, None otherwise
        """
        try:
            return self.match(syntax, query_string)
        except (ValueError, Exception):
            return None

    @property
    def state(self) -> BlockHandler:
        """Get the current block handler state"""
        return self.block_handler

    def update(self, block: BasicBlock) -> BasicBlock:
        """Update state with a block"""
        return self.block_handler.update(block)
