"""CFG helper functions - Python port of cfg-helper.ts"""
from tree_sitter import Node

from .control_flow.cfg import new_cfg_builder
from .control_flow.cfg_defs import CFG, BuilderOptions, merge_node_attrs
from .control_flow.graph_ops import simplify_cfg, trim_for
from .control_flow.call_processor import call_processor_for


def build_cfg(
    func: Node,
    language: str,
    simplify: bool = False,
    flat_switch: bool = True,
    ts_language=None
) -> CFG:
    """
    Build a CFG from a function AST node.

    Args:
        func: The function AST node
        language: The programming language
        simplify: Whether to simplify the CFG
        flat_switch: Whether to flatten switch statements
        ts_language: The tree-sitter Language object

    Returns:
        The constructed CFG
    """
    # Get call processor for the language (if available)
    call_processor = call_processor_for(language)

    options = BuilderOptions(
        flat_switch=flat_switch,
        call_processor=call_processor
    )

    builder = new_cfg_builder(language, options, ts_language)
    cfg = builder.build_cfg(func)

    # Trim unreachable nodes
    cfg = trim_for(cfg)

    # Optionally simplify
    if simplify:
        cfg = simplify_cfg(cfg, merge_node_attrs)

    return cfg
