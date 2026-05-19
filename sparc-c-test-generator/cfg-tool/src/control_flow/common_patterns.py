"""Common CFG patterns - Python port of common-patterns.ts"""
from tree_sitter import Node
from typing import Callable, Optional, List, Dict
from dataclasses import dataclass

from .cfg_defs import BasicBlock, NodeType, EdgeType, ExitStatement, Goto
from .generic_cfg_builder import Context, Extra
from .block_matcher import Match
from ..utils.hacks import tree_sitter_no_null_nodes
from ..utils.itertools_utils import last, pairwise, zip_arrays


def c_style_if_processor(query_string: str) -> Callable[[Node, Context], BasicBlock]:
    """Processor for C-style if statements"""

    def processor(if_syntax: Node, ctx: Context) -> BasicBlock:
        def get_ifs(current_syntax: Node) -> List[Match]:
            """Recursively collect all if-else if matches"""
            match = ctx.matcher.try_match(current_syntax, query_string)
            if not match:
                return []
            else_if_syntax = match.get_syntax("else-if")
            if not else_if_syntax:
                return [match]
            return [match] + get_ifs(else_if_syntax)

        all_ifs = get_ifs(if_syntax)
        blocks = [
            {
                'cond_block': if_match.get_block(if_match.require_syntax("cond")),
                'then_block': if_match.get_block(if_match.require_syntax("then")),
                'else_block': if_match.get_block(if_match.get_syntax("else-body"))
            }
            for if_match in all_ifs
        ]

        # Link syntax nodes
        for if_match, block_dict in zip_arrays(all_ifs, blocks):
            cond_block = block_dict['cond_block']
            ctx.link.syntax_to_node(if_match.require_syntax("if"), cond_block.entry)
            ctx.link.offset_to_syntax(
                if_match.require_syntax("closing-paren"),
                if_match.require_syntax("then")
            )

        for prev_if, this_if in pairwise(all_ifs):
            ctx.link.offset_to_syntax(
                prev_if.require_syntax("then"),
                this_if.require_syntax("if")
            )

        head_node = ctx.builder.add_node(
            NodeType.CONDITION,
            "if-else head",
            if_syntax.start_byte
        )
        merge_node = ctx.builder.add_node(
            NodeType.MERGE,
            "if-else merge",
            if_syntax.end_byte
        )

        # Connect first block
        if blocks and blocks[0]['cond_block'].entry:
            ctx.builder.add_edge(head_node, blocks[0]['cond_block'].entry)

        # Connect all condition/then blocks
        previous = None
        for block_dict in blocks:
            cond_block = block_dict['cond_block']
            then_block = block_dict['then_block']

            if previous and cond_block.entry:
                ctx.builder.add_edge(previous, cond_block.entry, EdgeType.ALTERNATIVE)

            if cond_block.exit and then_block.entry:
                ctx.builder.add_edge(cond_block.exit, then_block.entry, EdgeType.CONSEQUENCE)

            if then_block.exit:
                ctx.builder.add_edge(then_block.exit, merge_node)

            previous = cond_block.exit

        # Handle else block
        else_block = blocks[-1]['else_block'] if blocks else None
        if else_block:
            last_match = all_ifs[-1]
            else_syntax = last_match.require_syntax("else")
            ctx.link.syntax_to_node(else_syntax, else_block.entry)
            ctx.link.offset_to_syntax(last_match.require_syntax("then"), else_syntax)

            if previous and else_block.entry:
                ctx.builder.add_edge(previous, else_block.entry, EdgeType.ALTERNATIVE)
            if else_block.exit:
                ctx.builder.add_edge(else_block.exit, merge_node)
        elif previous:
            ctx.builder.add_edge(previous, merge_node, EdgeType.ALTERNATIVE)

        return ctx.state.update(BasicBlock(entry=head_node, exit=merge_node))

    return processor


@dataclass
class RangeForDefinition:
    """Definition for range-based for loop processor"""
    query: str
    body: str
    else_: Optional[str] = None
    header_end: str = ""


def for_each_loop_processor(definition: RangeForDefinition) -> Callable[[Node, Context], BasicBlock]:
    """Processor for for-each style loops"""

    def processor(for_node: Node, ctx: Context) -> BasicBlock:
        builder, matcher = ctx.builder, ctx.matcher
        match = matcher.match(for_node, definition.query)

        body_syntax = match.require_syntax(definition.body)
        else_syntax = match.get_syntax(definition.else_) if definition.else_ else None

        body_block = match.get_block(body_syntax)
        else_block = match.get_block(else_syntax)

        head_node = builder.add_node(NodeType.LOOP_HEAD, "loop head", for_node.start_byte)
        exit_node = builder.add_node(NodeType.FOR_EXIT, "loop exit", for_node.end_byte)

        ctx.link.syntax_to_node(for_node, head_node)
        ctx.link.offset_to_syntax(match.require_syntax(definition.header_end), body_syntax)

        # Build loop structure
        builder.add_edge(head_node, body_block.entry, EdgeType.CONSEQUENCE)
        if body_block.exit:
            builder.add_edge(body_block.exit, head_node)

        if else_block:
            builder.add_edge(head_node, else_block.entry, EdgeType.ALTERNATIVE)
            if else_block.exit:
                builder.add_edge(else_block.exit, exit_node)
        else:
            builder.add_edge(head_node, exit_node, EdgeType.ALTERNATIVE)

        # Handle continue/break
        label = ctx.extra.label if ctx.extra else None
        matcher.state.for_each_continue(lambda cn: builder.add_edge(cn, head_node), label)
        matcher.state.for_each_break(lambda bn: builder.add_edge(bn, exit_node), label)

        return matcher.update(BasicBlock(entry=head_node, exit=exit_node))

    return processor


def c_style_for_statement_processor(query_string: str) -> Callable[[Node, Context], BasicBlock]:
    """Processor for C-style for loops"""

    def processor(for_node: Node, ctx: Context) -> BasicBlock:
        match = ctx.matcher.match(for_node, query_string)

        init_syntax = match.get_syntax("init")
        cond_syntax = match.get_syntax("cond")
        update_syntax = match.get_syntax("update")
        body_syntax = match.require_syntax("body")

        init_block = match.get_block(init_syntax)
        cond_block = match.get_block(cond_syntax)
        update_block = match.get_block(update_syntax)
        body_block = match.get_block(body_syntax)

        entry_node = ctx.builder.add_node(NodeType.EMPTY, "loop head", for_node.start_byte)
        exit_node = ctx.builder.add_node(NodeType.FOR_EXIT, "loop exit", for_node.end_byte)
        head_node = ctx.builder.add_node(NodeType.LOOP_HEAD, "loop head", for_node.start_byte)

        ctx.link.syntax_to_node(for_node, entry_node)
        if cond_block:
            ctx.link.syntax_to_node(match.require_syntax("cond-semi"), cond_block.entry)

        close_parens = match.require_syntax("close-parens")

        # Link offsets
        if init_syntax:
            ctx.link.offset_to_syntax(init_syntax, match.require_syntax("init-semi"), reverse=True, include_to=True)
        if cond_syntax:
            ctx.link.offset_to_syntax(cond_syntax, match.require_syntax("cond-semi"), reverse=True, include_to=True)
        if not cond_syntax and init_syntax:
            ctx.link.offset_to_syntax(init_syntax, match.require_syntax("cond-semi"), include_to=True, reverse=True)
        if update_syntax:
            ctx.link.offset_to_syntax(update_syntax, close_parens, reverse=True, include_to=True)
        if cond_syntax and not update_syntax:
            ctx.link.offset_to_syntax(cond_syntax, close_parens, reverse=True, include_to=True)
        ctx.link.offset_to_syntax(close_parens, body_syntax)

        def chain_blocks(entry: Optional[str], blocks: List[Optional[BasicBlock]]) -> Optional[str]:
            """Chain blocks together with edges"""
            prev_exit = entry
            for block in blocks:
                if block is None:
                    continue
                if prev_exit and block.entry:
                    ctx.builder.add_edge(prev_exit, block.entry)
                prev_exit = block.exit
            return prev_exit

        # Build loop structure
        top_exit = chain_blocks(entry_node, [init_block])
        if cond_block:
            chain_blocks(top_exit, [cond_block])
            if cond_block.exit:
                ctx.builder.add_edge(cond_block.exit, body_block.entry, EdgeType.CONSEQUENCE)
                ctx.builder.add_edge(cond_block.exit, exit_node, EdgeType.ALTERNATIVE)
                chain_blocks(body_block.exit, [BasicBlock(entry=head_node, exit=head_node), update_block, cond_block])
        else:
            chain_blocks(top_exit, [body_block, BasicBlock(entry=head_node, exit=head_node), update_block, body_block])

        # Handle continue/break
        label = ctx.extra.label if ctx.extra else None
        ctx.matcher.state.for_each_continue(lambda cn: ctx.builder.add_edge(cn, head_node), label)
        ctx.matcher.state.for_each_break(lambda bn: ctx.builder.add_edge(bn, exit_node), label)

        return ctx.matcher.update(BasicBlock(entry=entry_node, exit=exit_node))

    return processor


def c_style_while_processor() -> Callable[[Node, Context], BasicBlock]:
    """Processor for while loops"""

    def processor(while_syntax: Node, ctx: Context) -> BasicBlock:
        query_string = """
        (while_statement
            condition: (_) @cond
            body: (_) @body
        ) @while
        """
        match = ctx.matcher.match(while_syntax, query_string)

        cond_syntax = match.require_syntax("cond")
        body_syntax = match.require_syntax("body")

        cond_block = match.get_block(cond_syntax)
        body_block = match.get_block(body_syntax)

        exit_node = ctx.builder.add_node(NodeType.FOR_EXIT, "loop exit", while_syntax.end_byte)

        if cond_block.exit:
            if body_block.entry:
                ctx.builder.add_edge(cond_block.exit, body_block.entry, EdgeType.CONSEQUENCE)
            ctx.builder.add_edge(cond_block.exit, exit_node, EdgeType.ALTERNATIVE)

        if cond_block.entry and body_block.exit:
            ctx.builder.add_edge(body_block.exit, cond_block.entry)

        # Handle continue/break
        label = ctx.extra.label if ctx.extra else None
        ctx.matcher.state.for_each_continue(
            lambda cn: ctx.builder.add_edge(cn, cond_block.entry) if cond_block.entry else None,
            label
        )
        ctx.matcher.state.for_each_break(lambda bn: ctx.builder.add_edge(bn, exit_node), label)

        ctx.link.syntax_to_node(body_syntax, body_block.entry)
        ctx.link.syntax_to_node(cond_syntax, cond_block.entry)
        ctx.link.syntax_to_node(while_syntax, cond_block.entry)

        return ctx.matcher.update(BasicBlock(entry=cond_block.entry, exit=exit_node))

    return processor


def c_style_do_while_processor() -> Callable[[Node, Context], BasicBlock]:
    """Processor for do-while loops"""

    def processor(do_syntax: Node, ctx: Context) -> BasicBlock:
        query_string = """
        (do_statement
            body: (_) @body
            condition: (_) @cond
        ) @do
        """
        match = ctx.matcher.match(do_syntax, query_string)

        cond_syntax = match.require_syntax("cond")
        body_syntax = match.require_syntax("body")

        cond_block = match.get_block(cond_syntax)
        body_block = match.get_block(body_syntax)

        exit_node = ctx.builder.add_node(NodeType.FOR_EXIT, "loop exit", do_syntax.end_byte)

        if cond_block.exit:
            if body_block.entry:
                ctx.builder.add_edge(cond_block.exit, body_block.entry, EdgeType.CONSEQUENCE)
            ctx.builder.add_edge(cond_block.exit, exit_node, EdgeType.ALTERNATIVE)

        if cond_block.entry and body_block.exit:
            ctx.builder.add_edge(body_block.exit, cond_block.entry)

        # Handle continue/break
        label = ctx.extra.label if ctx.extra else None
        ctx.matcher.state.for_each_continue(
            lambda cn: ctx.builder.add_edge(cn, cond_block.entry) if cond_block.entry else None,
            label
        )
        ctx.matcher.state.for_each_break(lambda bn: ctx.builder.add_edge(bn, exit_node), label)

        ctx.link.syntax_to_node(body_syntax, body_block.entry)
        ctx.link.syntax_to_node(cond_syntax, cond_block.entry)
        ctx.link.syntax_to_node(do_syntax, body_block.entry)

        return ctx.matcher.update(BasicBlock(entry=body_block.entry, exit=exit_node))

    return processor


def get_child_field_text(node: Node, field_name: str) -> str:
    """Get text of a child field"""
    child = node.child_by_field_name(field_name)
    if child and child.text:
        text = child.text
        return text.decode('utf-8') if isinstance(text, bytes) else text
    return ""


def process_goto_statement(goto_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a goto statement"""
    name = ""
    if goto_syntax.named_children and goto_syntax.named_children[0]:
        first_child = goto_syntax.named_children[0]
        if first_child.text:
            text = first_child.text
            name = text.decode('utf-8') if isinstance(text, bytes) else text

    goto_node = ctx.builder.add_node(NodeType.GOTO, name, goto_syntax.start_byte)
    ctx.link.syntax_to_node(goto_syntax, goto_node)
    return BasicBlock(
        entry=goto_node,
        exit=None,
        gotos=[Goto(node=goto_node, label=name)]
    )


def process_labeled_statement(label_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a labeled statement"""
    name = get_child_field_text(label_syntax, "label")
    label_node = ctx.builder.add_node(NodeType.LABEL, name, label_syntax.start_byte)
    ctx.link.syntax_to_node(label_syntax, label_node)

    if len(label_syntax.named_children) > 1:
        label_content_syntax = label_syntax.named_children[1]
        labeled_block = ctx.state.update(
            ctx.dispatch.single(label_content_syntax, Extra(label=name))
        )
        if labeled_block.entry:
            ctx.builder.add_edge(label_node, labeled_block.entry)
        return ctx.state.update(BasicBlock(
            entry=label_node,
            exit=labeled_block.exit,
            labels={name: label_node}
        ))

    return ctx.state.update(BasicBlock(
        entry=label_node,
        exit=label_node,
        labels={name: label_node}
    ))


def process_continue_statement(continue_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a continue statement"""
    continue_node = ctx.builder.add_node(NodeType.CONTINUE, "CONTINUE", continue_syntax.start_byte)
    ctx.link.syntax_to_node(continue_syntax, continue_node)
    return BasicBlock(
        entry=continue_node,
        exit=None,
        continues=[ExitStatement(from_node=continue_node)]
    )


def process_break_statement(break_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a break statement"""
    break_node = ctx.builder.add_node(NodeType.BREAK, "BREAK", break_syntax.start_byte)
    ctx.link.syntax_to_node(break_syntax, break_node)
    return BasicBlock(
        entry=break_node,
        exit=None,
        breaks=[ExitStatement(from_node=break_node)]
    )


def process_statement_sequence(syntax: Node, ctx: Context) -> BasicBlock:
    """Process a sequence of statements (compound statement)"""
    named_children = [child for child in syntax.named_children if child is not None]
    named_children = tree_sitter_no_null_nodes(named_children)
    block_block = ctx.dispatch.many(named_children, syntax)
    ctx.link.syntax_to_node(syntax, block_block.entry)
    return block_block


def process_return_statement(syntax: Node, ctx: Context) -> BasicBlock:
    """Process a return statement"""
    text = syntax.text
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    return_node = ctx.builder.add_node(NodeType.RETURN, text, syntax.start_byte)
    ctx.link.syntax_to_node(syntax, return_node)
    return BasicBlock(entry=return_node, exit=None)


def process_comment(comment_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a marker comment"""
    text = comment_syntax.text
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    comment_node = ctx.builder.add_node(NodeType.MARKER_COMMENT, text, comment_syntax.start_byte)
    ctx.link.syntax_to_node(comment_syntax, comment_node)

    if ctx.options.marker_pattern:
        import re
        match = re.match(ctx.options.marker_pattern, text)
        if match and len(match.groups()) > 0:
            marker = match.group(1)
            ctx.builder.add_marker(comment_node, marker)

    return BasicBlock(entry=comment_node, exit=comment_node)


def process_throw_statement(throw_syntax: Node, ctx: Context) -> BasicBlock:
    """Process a throw statement"""
    text = throw_syntax.text
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    throw_node = ctx.builder.add_node(NodeType.THROW, text, throw_syntax.start_byte)
    ctx.link.syntax_to_node(throw_syntax, throw_node)
    return BasicBlock(
        entry=throw_node,
        exit=None,
        function_exits=[throw_node]
    )
