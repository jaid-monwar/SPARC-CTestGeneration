"""C language CFG builder - Python port of cfg-c.ts"""
from tree_sitter import Node
from typing import Callable, Dict, List
from pathlib import Path

from .cfg_defs import BasicBlock, BuilderOptions, NodeType
from .generic_cfg_builder import Context, StatementHandlers, GenericCFGBuilder
from .common_patterns import (
    c_style_if_processor,
    c_style_for_statement_processor,
    c_style_while_processor,
    c_style_do_while_processor,
    process_break_statement,
    process_comment,
    process_continue_statement,
    process_goto_statement,
    process_labeled_statement,
    process_return_statement,
    process_statement_sequence,
    get_child_field_text
)
from .switch_utils import build_switch, collect_cases, SwitchOptions, CaseCollectionCallbacks
from ..utils.hacks import tree_sitter_no_null_nodes
from ..utils.query_utils import extract_captured_texts_by_capture_name


# Parser path (relative to this file)
PARSER_PATH = Path(__file__).parent.parent.parent / "parsers" / "tree-sitter-c.wasm"


def create_cfg_builder(options: BuilderOptions, language=None):
    """Create a C CFG builder"""
    return GenericCFGBuilder(get_statement_handlers(), options, language)


def get_statement_handlers() -> StatementHandlers:
    """Get statement handlers for C language"""
    process_if_statement = c_style_if_processor("""
        (if_statement
            condition: (_ ")" @closing-paren) @cond
            consequence: (_) @then
            alternative: (
                else_clause [
                    (if_statement) @else-if
                    (compound_statement) @else-body
                    (_) @else-body
                ]
            )? @else
        )@if
    """)

    process_for_statement = c_style_for_statement_processor("""
        (for_statement
            "(" @open-parens
            [
                initializer: (_ ";" @init-semi)? @init
                ";" @init-semi
            ]
            condition: (_)? @cond
            ";" @cond-semi
            update: (_)? @update
            ")" @close-parens
            body: (_) @body) @for
    """)

    named_handlers: Dict[str, Callable[[Node, Context], BasicBlock]] = {
        'compound_statement': process_statement_sequence,
        'if_statement': process_if_statement,
        'for_statement': process_for_statement,
        'while_statement': c_style_while_processor(),
        'do_statement': c_style_do_while_processor(),
        'switch_statement': process_switchlike,
        'return_statement': process_return_statement,
        'break_statement': process_break_statement,
        'continue_statement': process_continue_statement,
        'labeled_statement': process_labeled_statement,
        'goto_statement': process_goto_statement,
        'comment': process_comment,
    }

    return StatementHandlers(
        named=named_handlers,
        default=default_process_statement
    )


def default_process_statement(syntax: Node, ctx: Context) -> BasicBlock:
    """Default handler for unrecognized statements"""
    text = syntax.text
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    new_node = ctx.builder.add_node(NodeType.STATEMENT, text, syntax.start_byte)
    ctx.link.syntax_to_node(syntax, new_node)
    return BasicBlock(entry=new_node, exit=new_node)


# Switch statement handling
CASE_TYPES = {'case_statement'}


def get_cases(switch_syntax: Node) -> List[Node]:
    """Get all case nodes from a switch statement"""
    if len(switch_syntax.named_children) < 2:
        return []
    switch_body = switch_syntax.named_children[1]
    return [
        child for child in tree_sitter_no_null_nodes(switch_body.named_children)
        if child.type in CASE_TYPES
    ]


def parse_case(case_syntax: Node) -> dict:
    """Parse a case statement"""
    is_default = case_syntax.child_by_field_name("value") is None
    named_children = tree_sitter_no_null_nodes(case_syntax.named_children)
    consequence = named_children[0 if is_default else 1:]
    has_fallthrough = True  # C always has fallthrough potential
    return {
        'is_default': is_default,
        'consequence': consequence,
        'has_fallthrough': has_fallthrough
    }


class CCaseCallbacks:
    """Case collection callbacks for C"""

    def get_cases(self, switch_syntax: Node) -> List[Node]:
        return get_cases(switch_syntax)

    def parse_case(self, case_syntax: Node) -> dict:
        return parse_case(case_syntax)


def process_switchlike(switch_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a switch statement"""
    block_handler = ctx.matcher.state

    cases = collect_cases(switch_syntax, ctx, CCaseCallbacks())
    head_node = ctx.builder.add_node(
        NodeType.SWITCH_CONDITION,
        get_child_field_text(switch_syntax, "value"),
        switch_syntax.start_byte
    )
    ctx.link.syntax_to_node(switch_syntax, head_node)

    merge_node = ctx.builder.add_node(
        NodeType.SWITCH_MERGE,
        "",
        switch_syntax.end_byte
    )

    build_switch(cases, merge_node, head_node, SwitchOptions(), ctx)

    block_handler.for_each_break(lambda break_node: ctx.builder.add_edge(break_node, merge_node))

    # Link braces
    brace_match = ctx.matcher.match(
        switch_syntax,
        """
        (switch_statement
            body: (compound_statement "{" @opening-brace "}" @closing-brace)
        ) @switch
        """
    )
    opening_brace = brace_match.require_syntax("opening-brace")
    closing_brace = brace_match.require_syntax("closing-brace")

    case_syntax_many = get_cases(switch_syntax)
    if case_syntax_many:
        first_case = case_syntax_many[0]
        ctx.link.offset_to_syntax(opening_brace, first_case)

        last_case = case_syntax_many[-1]
        ctx.link.offset_to_syntax(last_case, closing_brace, reverse=True, include_to=True)

    return block_handler.update(BasicBlock(entry=head_node, exit=merge_node))


# Function name extraction
FUNCTION_QUERY = {
    'function_declarator': '(function_declarator declarator:(identifier)@name)',
    'capture_name': 'name'
}


def get_function_declarator(func_def: Node) -> Node:
    """Get the function_declarator node from a function_definition"""
    def find_declarators(node: Node) -> list:
        """Recursively find function_declarator nodes"""
        result = []
        if node.type == "function_declarator":
            result.append(node)
        for child in node.children:
            result.extend(find_declarators(child))
        return result

    body = func_def.child_by_field_name("body")

    # Find all function_declarator nodes before the body
    for node in find_declarators(func_def):
        if body and node.start_byte >= body.start_byte:
            continue
        decl = node.child_by_field_name("declarator")
        if decl and decl.type == "identifier":
            return node

    return None


def extract_c_function_name(func: Node) -> str:
    """Extract the function name from a C function definition"""
    declarator = get_function_declarator(func)
    if not declarator:
        return None

    names = extract_captured_texts_by_capture_name(
        declarator,
        FUNCTION_QUERY['function_declarator'],
        FUNCTION_QUERY['capture_name']
    )
    return names[0] if names else None


# Language definition
C_LANGUAGE_DEFINITION = {
    'wasm_path': str(PARSER_PATH),
    'create_cfg_builder': create_cfg_builder,
    'function_node_types': ['function_definition'],
    'extract_function_name': extract_c_function_name
}
