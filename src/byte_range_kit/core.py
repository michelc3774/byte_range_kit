from __future__ import annotations

import os
from dataclasses import dataclass
from typing import IO, Optional


class RangeError(ValueError):
    """Raised when a requested byte range is invalid for the underlying file."""


@dataclass(frozen=True)
class ReadResult:
    """The bytes read and the count actually consumed.

    ``count`` may be smaller than the requested length when the range reaches
    the end of the file. This is intentional: callers that need exact lengths
    should check ``count`` and raise their own error, rather than the reader
    guessing whether a short read is acceptable.
    """
    data: bytes
    count: int


class ByteRangeReader:
    """Read arbitrary byte ranges from a file without loading the whole file.

    Each call to ``read`` opens the file fresh, seeks to ``offset``, and reads
    up to ``length`` bytes. Opening per call avoids holding a file handle open
    between requests, which matters for long-lived services that would
    otherwise accumulate descriptors. The cost is an extra syscall per read;
    for the workloads this library targets (scattered ranges in large files)
    that is negligible compared to the I/O itself.
    """

    def __init__(self, path: str) -> None:
        self._path = path

    @property
    def path(self) -> str:
        return self._path

    def read(self, offset: int, length: int) -> ReadResult:
        if offset < 0:
            raise RangeError("offset must be non-negative, got %d" % offset)
        if length < 0:
            raise RangeError("length must be non-negative, got %d" % length)

        if length == 0:
            return ReadResult(data=b"", count=0)

        # Path.exists returns False for broken symlinks, but open() follows
        # the link and raises FileNotFoundError, so we skip the stat call.
        with open(self._path, "rb") as f:
            return self._read_from(f, offset, length)

    def _read_from(self, f: IO[bytes], offset: int, length: int) -> ReadResult:
        f.seek(offset, os.SEEK_SET)
        data = f.read(length)
        return ReadResult(data=data, count=len(data))
