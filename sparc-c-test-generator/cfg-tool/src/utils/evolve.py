"""Object evolution utility - Python port of evolve.ts"""
from typing import TypeVar, Dict, Any
import copy

T = TypeVar('T')


def evolve(obj: Dict[str, Any], attrs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new dictionary by cloning the original and applying partial updates.
    This function follows immutable update patterns.

    Args:
        obj: The original dictionary to be cloned
        attrs: Partial attributes to update on the new dictionary

    Returns:
        A new dictionary with the original properties and specified updates applied

    Example:
        user = {'name': 'Alice', 'age': 30}
        updated_user = evolve(user, {'age': 31})
        # Result: {'name': 'Alice', 'age': 31}
        # Original user remains {'name': 'Alice', 'age': 30}
    """
    new_obj = copy.deepcopy(obj)
    new_obj.update(attrs)
    return new_obj
