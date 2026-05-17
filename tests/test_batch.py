"""Batch: the rows + optional-schema container."""
import unittest

from cargodash import Batch, Schema


class TestBatch(unittest.TestCase):
    def test_len(self):
        self.assertEqual(len(Batch(rows=[{"a": 1}, {"a": 2}])), 2)

    def test_iter(self):
        b = Batch(rows=[{"a": 1}, {"a": 2}])
        self.assertEqual(list(b), [{"a": 1}, {"a": 2}])

    def test_default_is_empty_and_unschemaed(self):
        b = Batch()
        self.assertEqual(len(b), 0)
        self.assertIsNone(b.schema)

    def test_from_rows_consumes_iterable(self):
        s = Schema.of(a=int)
        b = Batch.from_rows(iter([{"a": 1}, {"a": 2}]), schema=s)
        self.assertEqual(b.rows, [{"a": 1}, {"a": 2}])
        self.assertEqual(b.schema, s)


if __name__ == "__main__":
    unittest.main()
