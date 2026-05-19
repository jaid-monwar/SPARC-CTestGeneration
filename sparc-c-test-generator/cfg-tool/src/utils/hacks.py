"""Utility hacks and workarounds - Python port of hacks.ts"""
from typing import List, Optional, TypeVar
from tree_sitter import Node

T = TypeVar('T')


def tree_sitter_no_null_nodes(nodes: List[Optional[Node]]) -> List[Node]:
    """
    Assert that there are no None values in a list of tree-sitter nodes.

    Args:
        nodes: List of potentially None nodes

    Returns:
        List of non-None nodes

    Raises:
        ValueError: If any None nodes are found
    """
    if any(node is None for node in nodes):
        raise ValueError("tree-sitter API actually had a None in the array!")
    return [node for node in nodes if node is not None]
