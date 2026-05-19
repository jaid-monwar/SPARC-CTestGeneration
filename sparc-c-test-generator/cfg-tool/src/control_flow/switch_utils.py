"""Switch statement utilities - Python port of switch-utils.ts"""
from tree_sitter import Node
from typing import List, Callable, Optional, Protocol
from dataclasses import dataclass

from .cfg_defs import EdgeType
from .generic_cfg_builder import Context
from ..utils.itertools_utils import pairwise


@dataclass
class SwitchOptions:
    """Options for building switch statements"""
    no_implicit_default: bool = False


@dataclass
class Case:
    """Represents a single case in a switch statement"""
    condition_entry: str
    condition_exit: str
    consequence_entry: str
    consequence_exit: Optional[str]
    alternative_exit: str
    has_fallthrough: bool
    is_default: bool
    is_empty: bool


class CaseCollectionCallbacks(Protocol):
    """Protocol for case collection callbacks"""

    def get_cases(self, switch_syntax: Node) -> List[Node]:
        """Get all case syntax nodes from a switch"""
        ...

    def parse_case(self, case_syntax: Node) -> dict:
        """Parse a single case syntax node"""
        ...


def build_switch(
    cases: List[Case],
    merge_node: str,
    switch_head_node: str,
    options: SwitchOptions,
    ctx: Context
) -> None:
    """
    Build a switch statement CFG.

    Args:
        cases: List of cases in the switch
        merge_node: The node where all cases merge
        switch_head_node: The switch condition node
        options: Switch building options
        ctx: CFG building context
    """
    fallthrough: Optional[str] = None
    has_default_case = False
    previous: Optional[str] = switch_head_node

    for this_case in cases:
        if ctx.options.flat_switch:
            ctx.builder.add_edge(switch_head_node, this_case.condition_entry)

            if this_case.is_empty and this_case.has_fallthrough:
                # Empty fallthrough case - link directly to next condition
                if fallthrough:
                    ctx.builder.add_edge(fallthrough, this_case.condition_entry)
                fallthrough = this_case.condition_exit
            else:
                ctx.builder.add_edge(this_case.condition_exit, this_case.consequence_entry)

                if fallthrough:
                    ctx.builder.add_edge(fallthrough, this_case.condition_entry)

                if not this_case.has_fallthrough and this_case.consequence_exit:
                    ctx.builder.add_edge(this_case.consequence_exit, merge_node, EdgeType.REGULAR)

                # Update for next case
                fallthrough = this_case.consequence_exit if this_case.has_fallthrough else None
        else:
            # Model switch as if-elif-else chain
            if fallthrough:
                ctx.builder.add_edge(fallthrough, this_case.consequence_entry)

            if previous and this_case.condition_entry:
                ctx.builder.add_edge(previous, this_case.condition_entry, EdgeType.ALTERNATIVE)

            if this_case.condition_exit:
                ctx.builder.add_edge(
                    this_case.condition_exit,
                    this_case.consequence_entry,
                    EdgeType.CONSEQUENCE
                )

            # Update for next case
            previous = None if this_case.is_default else this_case.alternative_exit

            if not this_case.has_fallthrough and this_case.consequence_exit:
                ctx.builder.add_edge(this_case.consequence_exit, merge_node, EdgeType.REGULAR)

            # Update for next case
            fallthrough = this_case.consequence_exit if this_case.has_fallthrough else None

        has_default_case = has_default_case or this_case.is_default

    # Connect last node to merge node
    if previous and not has_default_case and not options.no_implicit_default:
        ctx.builder.add_edge(previous, merge_node, EdgeType.ALTERNATIVE)

    if fallthrough:
        ctx.builder.add_edge(fallthrough, merge_node, EdgeType.REGULAR)


def collect_cases(
    switch_syntax: Node,
    ctx: Context,
    callbacks: CaseCollectionCallbacks
) -> List[Case]:
    """
    Collect all cases from a switch statement.

    Args:
        switch_syntax: The switch statement syntax node
        ctx: CFG building context
        callbacks: Callbacks for getting and parsing cases

    Returns:
        List of Case objects
    """
    cases: List[Case] = []
    case_syntax_many = callbacks.get_cases(switch_syntax)

    # Link offsets between consecutive cases
    for prev, curr in pairwise(case_syntax_many):
        ctx.link.offset_to_syntax(prev, curr)

    for case_syntax in case_syntax_many:
        parsed = callbacks.parse_case(case_syntax)
        is_default = parsed['is_default']
        consequence = parsed['consequence']
        has_fallthrough = parsed['has_fallthrough']

        # Get case condition text
        cond_text = "default"
        if not is_default and case_syntax.named_children:
            first_child = case_syntax.named_children[0]
            if first_child and first_child.text:
                text = first_child.text
                cond_text = text.decode('utf-8') if isinstance(text, bytes) else text

        condition_node = ctx.builder.add_node(
            "CASE_CONDITION",
            cond_text,
            case_syntax.start_byte
        )
        ctx.link.syntax_to_node(case_syntax, condition_node)

        consequence_block = ctx.state.update(ctx.dispatch.many(consequence, case_syntax))

        # Link the colon to the first consequence statement
        if consequence:
            colon_match = ctx.matcher.try_match(case_syntax, '(_ (":") @colon)')
            if colon_match:
                colon_syntax = colon_match.get_syntax("colon")
                if colon_syntax:
                    ctx.link.offset_to_syntax(colon_syntax, consequence[0])

        is_empty = len(consequence) == 0

        cases.append(Case(
            condition_entry=condition_node,
            condition_exit=condition_node,
            consequence_entry=consequence_block.entry,
            consequence_exit=consequence_block.exit,
            alternative_exit=condition_node,
            has_fallthrough=has_fallthrough,
            is_default=is_default,
            is_empty=is_empty
        ))

    return cases
