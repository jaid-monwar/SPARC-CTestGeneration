"""Parser loader - loads tree-sitter parsers"""
from pathlib import Path
from typing import Dict, Tuple, Any


def initialize_parser(language_name: str, wasm_path: str = None) -> Tuple:
    """
    Initialize a tree-sitter parser for a language.

    Args:
        language_name: Name of the language
        wasm_path: Path to the WASM parser file (optional, not used with tree-sitter-languages)

    Returns:
        Tuple of (Parser instance, Language instance)
    """
    lang_name = language_name.lower()
    
    # Method 1: Try tree-sitter-languages (works with 1.8.0 - 1.10.2)
    try:
        from tree_sitter_languages import get_language, get_parser
        lang = get_language(lang_name)
        parser = get_parser(lang_name)
        return parser, lang
    except Exception:
        pass
    
    # Method 2: Try tree-sitter 0.23+ with tree_sitter_c module
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_c
        
        language_capsule = tree_sitter_c.language()
        
        # Try with name argument (0.23+)
        try:
            lang = Language(language_capsule, lang_name)
        except TypeError:
            lang = Language(language_capsule)
        
        parser = Parser(lang)
        return parser, lang
    except Exception as e:
        raise ValueError(f"Failed to initialize parser for {language_name}: {e}")


def get_all_parsers() -> Dict[str, Any]:
    """
    Get parsers for all supported languages.

    Returns:
        Dictionary mapping language names to Parser instances
    """
    from ..control_flow.cfg import SUPPORTED_LANGUAGES, get_wasm_path

    parsers = {}
    for lang in SUPPORTED_LANGUAGES:
        wasm_path = get_wasm_path(lang)
        parsers[lang] = initialize_parser(lang, wasm_path)

    return parsers
