"""File parsing utilities - Python port of file-parsing.ts"""
from typing import Dict, List, Iterator
from pathlib import Path
from tree_sitter import Node, Parser

from ..control_flow.cfg import SUPPORTED_LANGUAGES, get_function_node_types


# File type mappings
FILE_TYPES = [
    {"ext": "c", "language": "C"},
    {"ext": "h", "language": "C"},
]

# Build extension to language map
EXT_TO_LANGUAGE: Dict[str, str] = {
    f".{ft['ext']}": ft['language']
    for ft in FILE_TYPES
}


def get_language(filename: str) -> str:
    """
    Get the language for a file based on its extension.

    Args:
        filename: The file path

    Returns:
        The language name

    Raises:
        ValueError: If the extension is not supported
    """
    ext = Path(filename).suffix.lower()
    language = EXT_TO_LANGUAGE.get(ext)
    if not language:
        raise ValueError(f"Unsupported extension {ext}")
    return language


def iter_functions(code: str, language: str, parser: Parser) -> Iterator[Node]:
    """
    Iterate over all function definitions in source code.

    Args:
        code: The source code
        language: The programming language
        parser: The tree-sitter parser

    Yields:
        Function AST nodes
    """
    tree = parser.parse(bytes(code, 'utf-8'))
    if not tree:
        return

    function_types = set(get_function_node_types(language))
    cursor = tree.walk()

    def visit_node() -> Iterator[Node]:
        """Recursively visit nodes"""
        if cursor.node.type in function_types:
            yield cursor.node

        if cursor.goto_first_child():
            yield from visit_node()
            while cursor.goto_next_sibling():
                yield from visit_node()
            cursor.goto_parent()

    yield from visit_node()
