import argparse
import bisect
import glob
import heapq
import json
import logging
import os
from enum import Enum, auto
from numbers import Number
from typing import (Any, Dict, Iterable, List, Mapping, Optional, Sequence,
                    Tuple, TypeVar, Union)

import torch

class Trim(Enum):
    """
    An enum denoting how to trim a Segment that is too long

    - **start**: trim the start of the segment
    - **end**: trim the end of the segment
    - **middle**: trim the middle of the segment
    - **none**: do not trim the segment
    """

    start = auto()
    end = auto()
    middle = auto()


### CLASS IndexedSet ########## 

DataType = TypeVar("DataType")


class IndexedSet(List[DataType]):
    """
    A class that makes indexing a unique sorted list easy. All the entries must
    have unique keys, if you try to insert an already existing key, it will
    raise an error.

    Loosely based on SortedCollection, which is referenced in the python docs
    for bisect.

    See: https://code.activestate.com/recipes/577197-sortedcollection/
    """

    def __init__(self, *iterable: Iterable[DataType], key=int):
        super().__init__()
        self._key = key
        self._keys: List[Any] = []

        # Ensure the list is in sorted order by inserting one at a time
        for value in tuple(*iterable):
            self.insert(value)

    def insert(self, value):
        """
        Insert into the set
        """
        key = self._key(value)
        idx = bisect.bisect_left(self._keys, key)
        if (
            idx != len(self._keys)
            and self[idx] == value  # pylint:disable=unsubscriptable-object
        ):
            # it's already in the set, no need to insert it
            return

        self._keys.insert(idx, key)
        super().insert(idx, value)  # pylint:disable=no-member

    def index(self, value: DataType) -> int:  # type: ignore
        """
        Find the index of the item in the set
        """
        key = self._key(value)
        idx = bisect.bisect_left(self._keys, key)
        if (
            idx != len(self._keys)
            and self[idx] == value  # pylint:disable=unsubscriptable-object
        ):
            return idx

        raise ValueError(f"{value} not in set")


class IndexedDict(Dict[str, DataType]):
    """
    A convenient wrapper around dict that allows integer-based indexing
    operations
    """

    indices: List[str]
    reverse_indices: Dict[str, int]

    def __init__(
        self, mapping: Union[Iterable[Tuple[str, DataType]], Mapping[str, DataType]]
    ):
        super().__init__()
        self.indices = []
        self.reverse_indices = {}

        if isinstance(mapping, Mapping):
            mapping = mapping.items()

        for idx, (key, value) in enumerate(mapping):
            self.indices.append(key)
            self.reverse_indices[key] = idx
            super().__setitem__(key, value)  # pylint:disable=no-member

    def __reduce__(self):
        return (type(self), (dict(self),))

    def __delitem__(self, key: str):
        raise RuntimeError("IndexedDict is immutable!")

    def __setitem__(self, key: str, value: DataType):
        raise RuntimeError("IndexedDict is immutable!")

    def index(self, key: str) -> int:
        """
        Return the index of the key
        """
        try:
            return self.reverse_indices[key]
        except KeyError:
            raise ValueError(f"{key} not in dict")


