import argparse
import bisect
import glob
import heapq
import json
import logging
import os
from enum import Enum, auto, unique
from numbers import Number
from typing import (Any, Dict, Iterable, List, Mapping, Optional, Sequence,
                    Tuple, TypeVar, Union)

import torch
import zlib
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import islice, zip_longest
from typing import (Any, Dict, Iterable, List, Optional, Sequence, Tuple,
                    TypeVar, Union)

from kiwisolver import Constraint, Solver, Variable, strength

from datastructures import (
    IndexedDict,
    IndexedSet,
    Trim,
)


class Segment(tuple):
    """
    This structure holds a sequence of token ids from the tokenizer vocabulary, along with a
    list of segment ids that modify the entire sequence of token ids.
    """

    # metadata
    segment_ids: Tuple[int, ...]
    separator: Optional[int]
    eos: Optional[int]

    # Layout related variables
    trim: Trim
    constrained: bool
    naive_max_length: int
    preferred_length: int
    length: Optional[Variable]

    # A constant defining the min length of a text segment (it can be shorter
    # if the underlying data is shorter than that constant).
    MIN_LENGTH = 100


    def __new__(
        cls,
        *iterable: Union[Iterable[int], Iterable["Segment"]],
        segment_ids: Iterable[int] = tuple(),
        separator: Optional[int] = None,
        eos: Optional[int] = None,
        preferred_length: int = 0,
        trim: Trim = Trim.end,
    ):
        """
        Create a Segment
        """
        self = super().__new__(cls, *iterable)  # type: ignore

        # Initialize the layout related variables before iterating over the
        # newly created tuple. It must be unconstrained to begin with.
        self.trim = trim
        self.length = None
        self.naive_max_length = -1
        self.preferred_length = preferred_length

        # Since the separator and eos effects the length, we must set it before
        # iterating over the Segment below.
        self.separator = separator
        self.eos = eos

        all_ints = all(isinstance(t, int) for t in self)
        all_segments = all(isinstance(t, Segment) for t in self)
        if not (all_ints or all_segments):
            raise ValueError(
                f"{cls.__name__}() only accepts a homogenous sequence of int or {cls.__name__}"
            )

        self.segment_ids = tuple(segment_ids)
        if not all(isinstance(t, int) for t in segment_ids):
            raise ValueError(f"{cls.__name__}() segment_ids must be int!")

        return self

    @property
    def hard_constraints(self) -> List[Constraint]:
        """
        Return a list of hard constraints defining the length of the segment
        """
        constraints: List[Constraint] = []
        for segment in self:
            if isinstance(segment, Segment):
                constraints.extend(segment.hard_constraints)

        if self.length:
            # Get the underlying length of the data
            length = self.unconstrained_length

            # Cannot be shorter than 1
            constraints.append((self.length >= 1) | strength.required)

            # Cannot be longer than the underlying length
            constraints.append((self.length <= length) | strength.required)

        return constraints

    @property
    def medium_constraints(self) -> List[Constraint]:
        """
        Return a list of constraints defining the length of the segment
        """
        constraints: List[Constraint] = []
        for segment in self:
            if isinstance(segment, Segment):
                constraints.extend(segment.medium_constraints)

        if self.length:
            # Get the underlying length of the data
            length = self.unconstrained_length

            # Resist shrinking below the underlying length
            constraints.append((self.length >= length) | strength.medium)

            # Try to stay close to the underlying length
            constraints.append((self.length == length) | strength.medium)

            # Resist shrinking below the min length a little more strongly
            constraints.append((self.length >= Segment.MIN_LENGTH) | strength.medium)

        return constraints

    @property
    def strong_constraints(self) -> List[Constraint]:
        """
        Return a list of constraints defining the length of the segment
        """
        constraints: List[Constraint] = []
        for segment in self:
            if isinstance(segment, Segment):
                constraints.extend(segment.strong_constraints)

        if self.length:
            # Very strongly try to stay close to the preferred length
            if self.preferred_length:
                constraints.append(
                    (self.length == self.preferred_length) | strength.create(10, 0, 0)
                )
            else:
                # Try to stay close to the min length a little more strongly
                constraints.append(
                    (self.length == Segment.MIN_LENGTH) | strength.strong
                )

        return constraints

    def __len__(self):
        """
        By default length returns the constrained length. To get the full
        length see Segement.unconstrained_length
        """
        unconstrained_length = self.unconstrained_length
        if self.naive_max_length >= 0:
            if not self.preferred_length:
                return min(unconstrained_length, Segment.MIN_LENGTH)

            return unconstrained_length

        if not self.length:
            return unconstrained_length

        return int(self.length.value()) or unconstrained_length

    def __getitem__(self, key):
        """
        Allow __getitem__ to support constraining the underlying sequence
        """
        return self._constrained_sequence[key]

    def __iter__(self):
        """
        Iterate over the constrained Segment
        """
        return iter(self._constrained_sequence)

    @property
    def _constrained_sequence(self):
        """
        Return the constrained segment
        """
        sequence = super().__getitem__(self._constrained_slice)
        if self.separator is not None:
            # If there is a separator it is always the first token
            sequence = (self.separator,) + sequence

            # By virtue of adding the separator, we may need to remove the last
            # element of the sequence, if it would cause the constrained
            # sequence to be too long
            sequence = sequence[: len(self)]

        if self.eos is not None:
            # By virtue of adding eos, we may need to remove the next to last
            # element of the sequence, if it would cause the constrained
            # sequence to be too long
            if len(sequence) + 1 > len(self):
                sequence = sequence[: len(self) - 1]

            # If we have an end of sequence token it is always last
            sequence = sequence + (self.eos,)

        return sequence

    @property
    def _constrained_slice(self) -> slice:
        """
        Compute the constrained slice for the Segment
        """
        length = len(self)
        if self.trim is Trim.end:
            return slice(length)

        if self.trim is Trim.start:
            return slice(-length, None)

        if self.trim is Trim.middle:
            remaining = self.unconstrained_length - length
            start = remaining // 2
            end = start - remaining
            return slice(start, end)

        raise RuntimeError("Unknown trim type!")

    @property
    def unconstrained_length(self):
        """
        Get the full unconstrained length of the Segment
        """
        return (
            super().__len__()
            + (0 if self.separator is None else 1)
            + (0 if self.eos is None else 1)
        )

    @property
    def token_segments(self):
        """
        A generator which yields all token ids within the segment recursively,
        along with their associated segment ids, which respects max length.
        """
        if self.length and self.naive_max_length >= 0:
            return islice(self._token_segments, self.naive_max_length)

        return self._token_segments

    @property
    def _token_segments(self):
        """
        A generator which yields all token ids within the segment recursively,
        along with their associated segment ids
        """
        for segment in self:
            if isinstance(segment, Segment):
                for (
                    token_id,
                    segment_ids,
                ) in segment._token_segments:  # pylint:disable=protected-access
                    yield token_id, self.segment_ids + segment_ids
            else:
                yield segment, self.segment_ids

    @property
    def length_variables(self):
        """
        A generator which yields all the length variables within the segment recursively
        """
        for segment in self:
            if isinstance(segment, Segment):
                yield from segment.length_variables

        if self.length:
            yield self.length

    @property
    def num_tokens(self):
        """
        Get the total number of tokens encapsulated by this Segment
        """
        num_tokens = 0
        for segment in self:
            if not isinstance(segment, Segment):
                # Since we do not mix tokens with nested Segment, we exit early
                # if we do not find a Segment as a minor optimization.
                break

            num_tokens += segment.num_tokens

        if not num_tokens:
            # If we didn't count any tokens, then this could be an empty
            # Segment, or its just make up of tokens without nested Segments.
            num_tokens += self.unconstrained_length

        return num_tokens

    def _mark_constrained(self, constrained: bool, max_length: int = -1):
        """
        Internal method to mark the Segment hierarchy as constrained or not.

        DO NOT CALL THIS DIRECTLY!
        """
        all_ints = False
        for segment in self:
            if not isinstance(segment, Segment):
                # __new__ only accepts a homogenous sequence of int or Segment,
                # so if an element is not a Segment, then this Segment must
                # contain only ints
                all_ints = True
                break

            segment._mark_constrained(  # pylint:disable=protected-access
                constrained, max_length
            )

        # If the segment only contains tokens ids, then it can be constrained.
        self.naive_max_length = max_length
        self.length = Variable() if constrained and all_ints else None

    def _constrain(self, max_length: int):
        """
        Internal method that constrains the Segment to a maximum length using kiwisolver.

        DO NOT CALL THIS DIRECTLY!
        """
        solver = Solver()

        # First add the hard constraints
        for constraint in self.hard_constraints:
            solver.addConstraint(constraint)

        # Want it to be exactly equal to the minimum of the max_length and
        # underlying number of tokens. This makes sure the constraint solver
        # doesn't try to short change and find a solution that uses less than
        # the available length.
        solver.addConstraint(
            sum(self.length_variables) == min(max_length, self.num_tokens)
        )

        # Then add the medium constraints
        for constraint in self.strong_constraints:
            solver.addConstraint(constraint)

        # Finally add the strong constraints
        for constraint in self.strong_constraints:
            solver.addConstraint(constraint)

        solver.updateVariables()

    @contextmanager
    def constraint(self, max_length: int, naive: bool = False):
        """
        A context manager that constrains the Segment, performs the necessary
        operation then unconstrains the Segment.
        """
        naive_max_length = max_length if naive else -1
        self._mark_constrained(True, naive_max_length)
        self._constrain(max_length)
        yield
        self._mark_constrained(False)

    def asdict(self, *, with_stats: bool = False) -> Dict[str, Any]:
        """
        Convert a sequence of annotated tokens into a dictionary of the form
        (where "stats" is optional):

        {
            "tokens": Tuple[int, ...],
            "segments": Tuple[
                {
                    "mask": Tuple[float, ...],
                    "values": Tuple[int, ...],
                },
                ...
            ]
            "stats": {
                int: count,
                ...
            }
        }
        """
        tokens, segments = zip(*self.token_segments)
        segment_dict = {
            "tokens": tokens,
            "segments": tuple(
                {
                    "mask": tuple(0.0 if s < 0 else 1.0 for s in segment),
                    # Cannot have a negative index, so just set it to 0, since
                    # it's going to get masked out anyway
                    "segments": tuple(0 if s < 0 else s for s in segment),
                }
                for segment in zip_longest(*segments, fillvalue=-1)
            ),
        }

        if with_stats:
            stats: Dict[int, int] = {}
            for _, segment_ids in self.token_segments:
                for segment_id in set(segment_ids):
                    stats[segment_id] = stats.get(segment_id, 0) + 1
            segment_dict["stats"] = stats

        return segment_dict

