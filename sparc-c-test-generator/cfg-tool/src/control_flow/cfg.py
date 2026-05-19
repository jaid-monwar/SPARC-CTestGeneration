"""Main CFG module - Python port of cfg.ts"""
from typing import List, Dict, Callable, Optional
from tree_sitter import Node

from .cfg_defs import BuilderOptions, CFG
from .cfg_c import C_LANGUAGE_DEFINITION


# Supported languages
SUPPORTED_LANGUAGES = ["C"]


def is_valid_language(language: str) -> bool:
    """Check if a language is supported"""
    return language in SUPPORTED_LANGUAGES


# Language definitions
LANGUAGE_DEFINITIONS: Dict[str, dict] = {
    "C": C_LANGUAGE_DEFINITION,
}


def new_cfg_builder(language: str, options: BuilderOptions, ts_language=None):
    """
    Create a new CFG builder for the given language.

    Args:
        language: The programming language
        options: Builder options
        ts_language: The tree-sitter Language object

    Returns:
        A CFG builder instance
    """
    if language not in LANGUAGE_DEFINITIONS:
        raise ValueError(f"Unsupported language: {language}")

    definition = LANGUAGE_DEFINITIONS[language]
    return definition['create_cfg_builder'](options, ts_language)


def extract_function_name(language: str, func: Node) -> Optional[str]:
    """
    Extract the function name from a function node.

    Args:
        language: The programming language
        func: The function AST node

    Returns:
        The function name, or None if not found
    """
    if language not in LANGUAGE_DEFINITIONS:
        raise ValueError(f"Unsupported language: {language}")

    definition = LANGUAGE_DEFINITIONS[language]
    return definition['extract_function_name'](func)


def get_function_node_types(language: str) -> List[str]:
    """Get the AST node types that represent functions for a language"""
    if language not in LANGUAGE_DEFINITIONS:
        raise ValueError(f"Unsupported language: {language}")

    definition = LANGUAGE_DEFINITIONS[language]
    return definition['function_node_types']


def get_wasm_path(language: str) -> str:
    """Get the WASM parser path for a language"""
    if language not in LANGUAGE_DEFINITIONS:
        raise ValueError(f"Unsupported language: {language}")

    definition = LANGUAGE_DEFINITIONS[language]
    return definition['wasm_path']
