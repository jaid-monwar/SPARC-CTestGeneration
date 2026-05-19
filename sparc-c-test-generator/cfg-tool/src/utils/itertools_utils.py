"""Iterator utility functions - Python port of itertools.ts"""
from typing import TypeVar, Iterator, Iterable, Tuple, List, Optional

T = TypeVar('T')
U = TypeVar('U')


def zip_arrays(*arrays: List) -> Iterator[Tuple]:
    """
    Zips multiple arrays together, creating tuples of elements at corresponding indices.
    Stops iterating when the shortest input array is exhausted.
    """
    if not arrays:
        return
    min_length = min(len(arr) for arr in arrays)
    for i in range(min_length):
        yield tuple(arr[i] for arr in arrays)


def pairwise(items: List[T]) -> Iterator[Tuple[T, T]]:
    """
    Generates adjacent pairs from an input list.

    Example:
        pairwise([1, 2, 3, 4]) -> [(1, 2), (2, 3), (3, 4)]
    """
    if len(items) < 2:
        return
    for i in range(len(items) - 1):
        yield (items[i], items[i + 1])


def chain(*arrays: Iterable[T]) -> Iterator[T]:
    """
    Chains multiple iterables into a single iterable sequence.
    """
    for array in arrays:
        yield from array


def last(items: List[T]) -> Optional[T]:
    """Returns the last element of a list, or None if empty."""
    return items[-1] if items else None


def maybe(value: Optional[T]) -> List[T]:
    """
    Converts an optional value to a list, handling None cases.

    Example:
        maybe(5) -> [5]
        maybe(None) -> []
    """
    return [value] if value is not None else []
