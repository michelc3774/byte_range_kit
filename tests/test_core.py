import os
import tempfile
import unittest

from byte_range_kit import ByteRangeReader, RangeError, ReadResult


class TestByteRangeReader(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(prefix="byte_range_kit_", suffix=".bin")
        with os.fdopen(fd, "wb") as f:
            f.write(b"Hello, World!")
        self.addCleanup(os.remove, self.path)

    def test_reads_subset_of_file(self):
        reader = ByteRangeReader(self.path)
        result = reader.read(0, 5)
        self.assertIsInstance(result, ReadResult)
        self.assertEqual(result.data, b"Hello")
        self.assertEqual(result.count, 5)

    def test_reads_from_nonzero_offset(self):
        reader = ByteRangeReader(self.path)
        result = reader.read(7, 5)
        self.assertEqual(result.data, b"World")
        self.assertEqual(result.count, 5)

    def test_zero_length_returns_empty_bytes(self):
        reader = ByteRangeReader(self.path)
        result = reader.read(0, 0)
        self.assertIsInstance(result, ReadResult)
        self.assertEqual(result.data, b"")
        self.assertEqual(result.count, 0)

    def test_zero_length_does_not_require_file_to_exist(self):
        reader = ByteRangeReader("/nonexistent/path/that/should/not/exist")
        result = reader.read(0, 0)
        self.assertEqual(result.data, b"")
        self.assertEqual(result.count, 0)

    def test_read_past_end_of_file_returns_partial_data(self):
        reader = ByteRangeReader(self.path)
        result = reader.read(7, 100)
        self.assertEqual(result.data, b"World!")
        self.assertEqual(result.count, 6)

    def test_read_from_eof_returns_empty_bytes(self):
        reader = ByteRangeReader(self.path)
        result = reader.read(13, 5)
        self.assertEqual(result.data, b"")
        self.assertEqual(result.count, 0)

    def test_negative_offset_raises_range_error(self):
        reader = ByteRangeReader(self.path)
        with self.assertRaises(RangeError):
            reader.read(-1, 5)

    def test_negative_length_raises_range_error(self):
        reader = ByteRangeReader(self.path)
        with self.assertRaises(RangeError):
            reader.read(0, -1)

    def test_negative_length_raises_range_error_even_when_offset_invalid(self):
        reader = ByteRangeReader(self.path)
        with self.assertRaises(RangeError):
            reader.read(-5, -1)

    def test_read_from_nonexistent_file_raises_filenotfound(self):
        reader = ByteRangeReader("/nonexistent/path/that/should/not/exist")
        with self.assertRaises(FileNotFoundError):
            reader.read(0, 5)

    def test_path_property_exposes_constructor_argument(self):
        reader = ByteRangeReader(self.path)
        self.assertEqual(reader.path, self.path)

    def test_multiple_reads_are_independent(self):
        reader = ByteRangeReader(self.path)
        first = reader.read(0, 5)
        second = reader.read(7, 5)
        self.assertEqual(first.data, b"Hello")
        self.assertEqual(second.data, b"World")

    def test_full_file_read(self):
        reader = ByteRangeReader(self.path)
        result = reader.read(0, 13)
        self.assertEqual(result.data, b"Hello, World!")
        self.assertEqual(result.count, 13)

    def test_empty_file(self):
        fd, empty_path = tempfile.mkstemp(prefix="byte_range_kit_empty_")
        os.close(fd)
        self.addCleanup(os.remove, empty_path)
        reader = ByteRangeReader(empty_path)
        result = reader.read(0, 5)
        self.assertEqual(result.data, b"")
        self.assertEqual(result.count, 0)


if __name__ == "__main__":
    unittest.main()
