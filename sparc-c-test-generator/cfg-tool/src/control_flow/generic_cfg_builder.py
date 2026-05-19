"""Generic CFG builder - Python port of generic-cfg-builder.ts"""
from tree_sitter import Node
from typing import Callable, Optional, Dict, List, Protocol
from dataclasses import dataclass

from .builder import Builder
from .block_matcher import BlockMatcher
from .node_mapper import NodeMapper
from .cfg_defs import BasicBlock, BlockHandler, CFG, BuilderOptions, NodeType
from ..utils.hacks import tree_sitter_no_null_nodes
from ..utils.itertools_utils import pairwise


@dataclass
class Extra:
    """Extra context for statement processing"""
    label: Optional[str] = None


class Dispatch(Protocol):
    """Protocol for dispatching AST nodes"""

    def single(self, syntax: Optional[Node], extra: Optional[Extra] = None) -> BasicBlock:
        """Process a single AST node"""
        ...

    def many(self, statements: List[Node], parent: Node) -> BasicBlock:
        """Process multiple AST nodes"""
        ...


class Link(Protocol):
    """Protocol for linking nodes"""

    def syntax_to_node(self, syntax: Node, node: str) -> None:
        """Link AST node to CFG node"""
        ...

    def offset_to_syntax(
        self,
        from_node: Node,
        to_node: Node,
        reverse: bool = False,
        include_to: bool = False,
        include_from: bool = False
    ) -> None:
        """Link offsets to AST nodes"""
        ...


@dataclass
class Context:
    """Context for CFG building"""
    builder: Builder
    options: BuilderOptions
    matcher: BlockMatcher
    dispatch: Dispatch
    state: BlockHandler
    link: Link
    extra: Optional[Extra] = None
    call_processor: Optional[Callable] = None


# Type for statement handlers
StatementHandler = Callable[[Node, Context], BasicBlock]


@dataclass
class StatementHandlers:
    """Maps AST node types to handler functions"""
    named: Dict[str, StatementHandler]
    default: StatementHandler


class DispatchImpl:
    """Implementation of Dispatch protocol"""

    def __init__(self, builder: 'GenericCFGBuilder'):
        self.builder = builder

    def single(self, syntax: Optional[Node], extra: Optional[Extra] = None) -> BasicBlock:
        if syntax is None:
            raise ValueError("Cannot dispatch None syntax node")
        return self.builder._dispatch_single(syntax, extra)

    def many(self, statements: List[Node], parent: Node) -> BasicBlock:
        return self.builder._dispatch_many(statements, parent)


class LinkImpl:
    """Implementation of Link protocol"""

    def __init__(self, node_mapper: NodeMapper):
        self.node_mapper = node_mapper

    def syntax_to_node(self, syntax: Node, node: str) -> None:
        self.node_mapper.link_syntax_to_node(syntax, node)

    def offset_to_syntax(
        self,
        from_node: Node,
        to_node: Node,
        reverse: bool = False,
        include_to: bool = False,
        include_from: bool = False
    ) -> None:
        self.node_mapper.link_offset_to_syntax(
            from_node, to_node, reverse, include_to, include_from
        )


class GenericCFGBuilder:
    """Generic framework for building CFGs from tree-sitter ASTs"""

    def __init__(self, handlers: StatementHandlers, options: BuilderOptions, language=None):
        self.builder = Builder()
        self.options = options
        self.handlers = handlers
        self.node_mapper = NodeMapper()
        self.language = language

    def build_cfg(self, function_node: Node) -> CFG:
        """
        Build a CFG from a function AST node.

        Args:
            function_node: The function's AST node

        Returns:
            The constructed CFG
        """
        # Create START node
        start_node = self.builder.add_node(
            NodeType.START,
            "START",
            function_node.start_byte
        )
        self.node_mapper.link_syntax_to_node(function_node, start_node)

        # Get function body
        body_syntax = function_node.child_by_field_name("body")

        if body_syntax:
            block_handler = BlockHandler()

            # Get named children, filtering out None values
            named_children = [child for child in body_syntax.named_children if child is not None]
            named_children = tree_sitter_no_null_nodes(named_children)

            # Process the body
            body_block = block_handler.update(
                self._dispatch_many(named_children, body_syntax)
            )

            # Process gotos
            block_handler.process_gotos(
                lambda goto_node, label_node: self.builder.add_edge(goto_node, label_node)
            )

            # Create END node
            end_node = self.builder.add_node(
                NodeType.RETURN,
                "implicit return",
                function_node.end_byte
            )

            # Connect nodes
            if body_block.entry:
                self.builder.add_edge(start_node, body_block.entry)
            if body_block.exit:
                self.builder.add_edge(body_block.exit, end_node)

            # Link the end of the function to the last statement
            if named_children:
                last_statement = named_children[-1]
                self.node_mapper.link_offset_to_syntax(
                    last_statement,
                    function_node,
                    include_to=True,
                    reverse=True
                )

        return CFG(
            graph=self.builder.get_graph(),
            entry=start_node,
            offset_to_node=self.node_mapper.get_index_mapping(function_node)
        )

    def _dispatch_single(self, syntax: Node, extra: Optional[Extra] = None) -> BasicBlock:
        """Process a single AST node"""
        handler = self.handlers.named.get(syntax.type, self.handlers.default)
        matcher = BlockMatcher(self._dispatch_single, self.language)

        dispatch = DispatchImpl(self)
        link = LinkImpl(self.node_mapper)

        ctx = Context(
            builder=self.builder,
            matcher=matcher,
            state=matcher.state,
            options=self.options,
            dispatch=dispatch,
            link=link,
            extra=extra,
            call_processor=self.options.call_processor
        )

        return handler(syntax, ctx)

    def _dispatch_many(self, statements: List[Node], parent: Node) -> BasicBlock:
        """Process multiple AST nodes"""
        block_handler = BlockHandler()

        # Filter out comments unless they match the marker pattern
        code_statements = []
        for syntax in statements:
            if syntax.type != "comment":
                code_statements.append(syntax)
            elif self.options.marker_pattern:
                import re
                if re.match(self.options.marker_pattern, syntax.text.decode('utf-8') if isinstance(syntax.text, bytes) else syntax.text):
                    code_statements.append(syntax)

        # Handle empty blocks
        if not code_statements:
            empty_node = self.builder.add_node(
                NodeType.EMPTY,
                "empty block",
                parent.start_byte
            )
            return BasicBlock(entry=empty_node, exit=empty_node)

        # Process all statements
        blocks = [
            block_handler.update(self._dispatch_single(statement))
            for statement in code_statements
        ]

        # Link offsets between consecutive statements
        for prev, curr in pairwise(code_statements):
            self.node_mapper.link_offset_to_syntax(prev, curr)

        # Connect blocks with edges
        for (prev_block, curr_block) in pairwise(blocks):
            if prev_block.exit:
                self.builder.add_edge(prev_block.exit, curr_block.entry)

        # Return combined block
        return block_handler.update(
            BasicBlock(
                entry=blocks[0].entry,
                exit=blocks[-1].exit if blocks else None
            )
        )
