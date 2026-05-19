"""Range-based lookup data structure - Python port of ranges.ts"""
from typing import TypeVar, Generic, List, Tuple, Optional, Iterator, Callable
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class SimpleRange(Generic[T]):
    """A simple range with a start position and a value."""
    start: int
    value: T


class Lookup(Generic[T]):
    """
    A data structure for efficient range-based value lookup.

    This allows mapping code offsets to values (like AST nodes or CFG nodes)
    in a hierarchical manner where smaller ranges can exist within larger ranges.
    """

    def __init__(self, initial_value: T):
        self.ranges: List[SimpleRange[T]] = [SimpleRange(start=0, value=initial_value)]

    def add(self, start: int, stop: int, value: T) -> None:
        """
        Add a new range to the lookup.

        Args:
            start: Start position of the range
            stop: End position of the range
            value: Value to associate with this range
        """
        splice_at, to_splice, delete_count = self._pre_add_range(start, stop, value)
        self.ranges[splice_at:splice_at + delete_count] = to_splice

    def _pre_add_range(self, start: int, stop: int, value: T) -> Tuple[int, List[SimpleRange[T]], int]:
        """Prepare range insertion by finding the splice position."""
        # Find the last range whose start is <= our start
        splice_at = -1
        for i in range(len(self.ranges) - 1, -1, -1):
            if start >= self.ranges[i].start:
                splice_at = i
                break

        if splice_at == -1:
            raise ValueError("Could not find splice position")

        # Check if we overflow into the next range
        if splice_at + 1 < len(self.ranges) and stop > self.ranges[splice_at + 1].start:
            raise ValueError(
                f"Cannot insert range at ({start}, {stop}), "
                f"overflows into range starting at {self.ranges[splice_at + 1].start}"
            )

        # Create the ranges to splice in
        to_splice = [
            SimpleRange(start=start, value=value),
            SimpleRange(start=stop, value=self.ranges[splice_at].value)
        ]

        # If we're replacing the start of an existing range
        if self.ranges[splice_at].start == start:
            return splice_at, to_splice, 1

        return splice_at + 1, to_splice, 0

    def get(self, position: int) -> T:
        """
        Get the value at the given position.

        Args:
            position: The position to query (must be >= 0)

        Returns:
            The value at the given position
        """
        if position < 0:
            raise ValueError("Position must be >= 0")

        # Find the last range whose start is <= position
        for i in range(len(self.ranges) - 1, -1, -1):
            if position >= self.ranges[i].start:
                return self.ranges[i].value

        raise ValueError(f"Failed to find value at given position {position}")

    def map_values(self, fn: Callable[[T], 'U']) -> 'Lookup[U]':
        """
        Create a new Lookup by applying a function to all values.

        Args:
            fn: Function to apply to each value

        Returns:
            New Lookup with transformed values
        """
        lookup = Lookup(fn(self.get(0)))
        lookup.ranges = [
            SimpleRange(start=r.start, value=fn(r.value))
            for r in self.ranges
        ]
        return lookup

    def __iter__(self) -> Iterator[Tuple[int, Optional[int], T]]:
        """Iterate over ranges as (start, stop, value) tuples."""
        for i in range(len(self.ranges)):
            start = self.ranges[i].start
            stop = self.ranges[i + 1].start if i + 1 < len(self.ranges) else None
            value = self.ranges[i].value
            yield (start, stop, value)

    def values(self) -> List[T]:
        """Get all values in the lookup."""
        return [r.value for r in self.ranges]

    def clone(self) -> 'Lookup[T]':
        """Create a shallow copy of this Lookup."""
        lookup = Lookup(self.get(0))
        lookup.ranges = self.ranges.copy()
        return lookup
