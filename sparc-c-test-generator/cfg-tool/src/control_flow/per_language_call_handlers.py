"""Per-language call handlers - Python port of per-language-call-handlers.ts"""
from typing import Dict, List, Literal
from dataclasses import dataclass


# Type for handler classification
HandlerType = Literal["TERMINATE", "ASSERT"]


@dataclass
class CallHandler:
    """Configuration for a call handler"""
    pattern: str  # Wildcard pattern for function name
    is_: HandlerType  # Type of handler (TERMINATE or ASSERT)


# Per-language call handlers
# Maps language names to lists of call handlers
PER_LANGUAGE_HANDLERS: Dict[str, List[CallHandler]] = {
    # C handlers - standard library functions that terminate
    "C": [
        CallHandler(pattern="exit", is_="TERMINATE"),
        CallHandler(pattern="_Exit", is_="TERMINATE"),
        CallHandler(pattern="abort", is_="TERMINATE"),
        CallHandler(pattern="quick_exit", is_="TERMINATE"),
        CallHandler(pattern="assert", is_="ASSERT"),
    ],
}
