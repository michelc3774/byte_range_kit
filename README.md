# byte_range_kit

Reads arbitrary byte ranges from large files without loading the entire file into memory.

```python
import tempfile
import os
from byte_range_kit import ByteRangeReader

fd, path = tempfile.mkstemp(suffix=".bin")
with os.fdopen(fd, "wb") as f:
    f.write(b"\x00" * 2097152)  # 2 MiB of data

reader = ByteRangeReader(path)
result = reader.read(offset=1048576, length=4096)
# result.data is bytes, result.count is the number of bytes actually read
os.remove(path)
```

## Why

For applications that need scattered, small reads from a large file (index lookups, binary format probes, sparse sampling), loading the whole file is wasteful and, for multi-gigabyte files, impossible. This library opens the file per read, seeks to the requested offset, and returns exactly the bytes requested. No caching, no background threads, no mmap — the minimum surface area to do this one job.

The trade-off: each read pays an `open`/`close` pair. For workloads with many sequential reads of the same file, a caller that keeps a file handle open will outperform this. This library targets scattered, infrequent access where descriptor lifetime is a bigger concern than syscall overhead.

## Edge cases

- A range that extends past the end of the file returns a short `ReadResult` (``count`` less than the requested length, `data` truncated accordingly). The library does not treat this as an error; callers that need exact-length reads should check `result.count`.
- `length == 0` returns empty bytes without touching the filesystem, so it is safe even on paths that do not exist.
- `offset == file_size` returns empty bytes rather than raising.
- Negative `offset` or `length` raises `RangeError`.
- Reads from a nonexistent file (with positive `length`) raise `FileNotFoundError`.
