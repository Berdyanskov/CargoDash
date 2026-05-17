"""RawDataSource and DataOutput: the jsonl read/write endpoints."""
import json
import tempfile
import unittest
from pathlib import Path

from cargodash import RawDataSource, DataOutput, Schema, Batch


class TestRawDataSource(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "data.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rows):
        with open(self.path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def test_batches_respect_batch_size(self):
        self._write([{"v": i} for i in range(10)])
        src = RawDataSource(str(self.path), batch_size=3)
        self.assertEqual([len(b) for b in src.iter_batches()], [3, 3, 3, 1])

    def test_blank_lines_are_skipped(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('{"v": 1}\n\n   \n{"v": 2}\n')
        src = RawDataSource(str(self.path), batch_size=10)
        rows = [r for b in src.iter_batches() for r in b]
        self.assertEqual(rows, [{"v": 1}, {"v": 2}])

    def test_empty_file_yields_no_batches(self):
        self._write([])
        src = RawDataSource(str(self.path), batch_size=4)
        self.assertEqual(list(src.iter_batches()), [])

    def test_output_schema_attached_to_each_batch(self):
        self._write([{"v": 1}, {"v": 2}])
        s = Schema.of(v=int)
        src = RawDataSource(str(self.path), schema=s, batch_size=1)
        self.assertTrue(all(b.schema == s for b in src.iter_batches()))


class TestDataOutput(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # Nested path: open() must create the parent directory.
        self.path = Path(self._tmp.name) / "nested" / "out.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_rows_and_creates_parent_dir(self):
        sink = DataOutput(str(self.path))
        sink.open()
        try:
            sink.process(Batch(rows=[{"v": 1}, {"v": 2}]))
        finally:
            sink.close()
        with open(self.path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(rows, [{"v": 1}, {"v": 2}])

    def test_process_produces_no_downstream_output(self):
        sink = DataOutput(str(self.path))
        sink.open()
        try:
            self.assertEqual(list(sink.process(Batch(rows=[{"v": 1}]))), [])
        finally:
            sink.close()

    def test_preserve_order_is_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            DataOutput(str(self.path), preserve_order=True)


if __name__ == "__main__":
    unittest.main()
