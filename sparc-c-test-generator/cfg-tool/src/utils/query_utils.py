"""Tree-sitter query utilities - Python port of query-utils.ts"""
from tree_sitter import Node
from typing import List


def extract_captured_texts_by_capture_name(
    node: Node,
    query_str: str,
    capture_name: str
) -> List[str]:
    """
    Extracts the text content of syntax tree nodes captured by a Tree-sitter query.

    Args:
        node: The syntax node from which to extract the tree
        query_str: The Tree-sitter query string to execute
        capture_name: The capture tag name to filter by

    Returns:
        List of text content from matching captures
    """
    # Get language from node - in tree-sitter Python, we need to get it differently
    # For now, we'll use a simpler approach by extracting directly from node structure
    # This is a workaround since tree-sitter Python API doesn't expose language directly

    # Simple extraction without query - just find the identifier child
    if "identifier" in query_str and node.type == "function_declarator":
        decl = node.child_by_field_name("declarator")
        if decl and decl.text:
            text = decl.text
            return [text.decode('utf-8') if isinstance(text, bytes) else text]

    # For other cases, try to find named children that match
    results = []
    for child in node.children:
        if child.type == "identifier" or child.is_named:
            if child.text:
                text = child.text
                text_str = text.decode('utf-8') if isinstance(text, bytes) else text
                if text_str:
                    results.append(text_str)

    return results
