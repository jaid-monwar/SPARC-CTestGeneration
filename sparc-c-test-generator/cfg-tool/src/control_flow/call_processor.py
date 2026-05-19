"""Call processor - Python port of call-processor.ts"""
from typing import Optional, Callable, TYPE_CHECKING
from tree_sitter import Node

from .cfg_defs import BasicBlock, NodeType, EdgeType
from .per_language_call_handlers import PER_LANGUAGE_HANDLERS, CallHandler, HandlerType
from .wildcard import match_wildcard

if TYPE_CHECKING:
    from .generic_cfg_builder import Context


# Type alias for call processor function
CallProcessor = Callable[[Node, str, 'Context'], Optional[BasicBlock]]


def match_handler(
    function_name: str,
    handlers: list[CallHandler]
) -> Optional[HandlerType]:
    """
    Find a handler that matches the function name.

    Args:
        function_name: The name of the function being called
        handlers: List of call handlers to check

    Returns:
        The handler type if a match is found, None otherwise
    """
    for handler in handlers:
        if match_wildcard(handler.pattern, function_name):
            return handler.is_
    return None


def call_processor_for(language: str) -> Optional[CallProcessor]:
    """
    Get a call processor for the specified language.

    Args:
        language: The programming language

    Returns:
        A call processor function if handlers exist for the language, None otherwise
    """
    handlers = PER_LANGUAGE_HANDLERS.get(language)
    if not handlers:
        return None
    return call_processor_factory(handlers)


def call_processor_factory(handlers: list[CallHandler]) -> CallProcessor:
    """
    Create a call processor from a list of handlers.

    Args:
        handlers: List of call handlers

    Returns:
        A call processor function
    """

    def processor(
        node: Node,
        function_name: str,
        ctx: 'Context'
    ) -> Optional[BasicBlock]:
        """
        Process a function call and potentially create special CFG nodes.

        Args:
            node: The syntax node for the call
            function_name: The name of the function being called
            ctx: The CFG building context

        Returns:
            A BasicBlock if this is a special call, None otherwise
        """
        handler_type = match_handler(function_name, handlers)

        if handler_type == "TERMINATE":
            # Create a terminating node (like exit(), abort())
            terminate_node = ctx.builder.add_node(
                NodeType.EXIT_PROCESS,
                f"Call to {function_name}",
                node.start_byte
            )
            return BasicBlock(
                entry=terminate_node,
                exit=None,  # No exit since it terminates
                function_exits=[terminate_node]
            )

        elif handler_type == "ASSERT":
            # Create assert nodes with condition, throw, and merge
            condition_node = ctx.builder.add_node(
                NodeType.ASSERT_CONDITION,
                f"Assert from: {function_name}",
                node.start_byte
            )
            raise_node = ctx.builder.add_node(
                NodeType.THROW,
                f"Assert from: {function_name}",
                node.start_byte
            )
            happy_node = ctx.builder.add_node(
                NodeType.MERGE,
                "Assert successful",
                node.start_byte
            )

            # Connect the nodes
            ctx.builder.add_edge(condition_node, raise_node, EdgeType.ALTERNATIVE)
            ctx.builder.add_edge(condition_node, happy_node, EdgeType.CONSEQUENCE)

            return BasicBlock(
                entry=condition_node,
                exit=happy_node,  # Continue execution if assert passes
                function_exits=[raise_node]  # Mark the assert failure path
            )

        # Not a special call
        return None

    return processor
