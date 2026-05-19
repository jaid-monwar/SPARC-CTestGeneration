"""Wildcard pattern matching - Python port of wildcard.ts"""
import re


def match_wildcard(pattern: str, search_string: str) -> bool:
    """
    Match a wildcard pattern against a search string.

    Wildcards (*) match any sequence of characters.

    Args:
        pattern: Pattern with wildcards (e.g., "sys.*", "self.assert*")
        search_string: String to match against

    Returns:
        True if the pattern matches the search string

    Examples:
        >>> match_wildcard("sys.*", "sys.exit")
        True
        >>> match_wildcard("self.assert*", "self.assertTrue")
        True
        >>> match_wildcard("panic", "panic")
        True
    """
    # Escape special regex characters except *
    # Split by * to preserve wildcard positions
    parts = pattern.split('*')

    # Escape each part for regex
    escaped_parts = [re.escape(part) for part in parts]

    # Join with .* to match any characters
    regex_pattern = '.*'.join(escaped_parts)

    # Anchor the pattern to match the entire string
    regex_pattern = f'^{regex_pattern}$'

    return bool(re.match(regex_pattern, search_string))
