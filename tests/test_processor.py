"""Processor: sample-mode and batch-mode transforms."""
import unittest

from cargodash import Processor, Schema, Batch


def _run(processor, batch):
    """Drive process() and return the list of (port, batch) tuples."""
    return list(processor.process(batch))


class TestProcessorSampleMode(unittest.TestCase):
    def test_one_to_one_transform(self):
        p = Processor(lambda r: {"v": r["v"] * 2})
        out = _run(p, Batch(rows=[{"v": 1}, {"v": 2}]))
        self.assertEqual(len(out), 1)
        port, batch = out[0]
        self.assertEqual(port, Processor.DEFAULT_PORT)
        self.assertEqual([r["v"] for r in batch.rows], [2, 4])

    def test_filter_drops_rows_returning_none(self):
        p = Processor(lambda r: r if r["v"] > 1 else None)
        port, batch = _run(p, Batch(rows=[{"v": 0}, {"v": 1}, {"v": 2}]))[0]
        self.assertEqual([r["v"] for r in batch.rows], [2])

    def test_filtering_every_row_yields_nothing(self):
        p = Processor(lambda r: None)
        self.assertEqual(_run(p, Batch(rows=[{"v": 1}, {"v": 2}])), [])

    def test_one_to_many_augmentation(self):
        p = Processor(lambda r: [{"v": r["v"]}, {"v": r["v"] + 100}])
        port, batch = _run(p, Batch(rows=[{"v": 1}, {"v": 2}]))[0]
        self.assertEqual([r["v"] for r in batch.rows], [1, 101, 2, 102])

    def test_intra_batch_workers_preserve_row_order(self):
        p = Processor(lambda r: {"v": r["v"]}, intra_batch_workers=4)
        port, batch = _run(p, Batch(rows=[{"v": i} for i in range(20)]))[0]
        self.assertEqual([r["v"] for r in batch.rows], list(range(20)))

    def test_explicit_output_schema_is_attached(self):
        s = Schema.of(v=int)
        p = Processor(lambda r: {"v": r["v"]}, output_schema=s)
        port, batch = _run(p, Batch(rows=[{"v": 1}]))[0]
        self.assertEqual(batch.schema, s)

    def test_falls_back_to_input_batch_schema(self):
        s = Schema.of(v=int)
        p = Processor(lambda r: {"v": r["v"]})  # no output_schema
        port, batch = _run(p, Batch(rows=[{"v": 1}], schema=s))[0]
        self.assertEqual(batch.schema, s)


class TestProcessorBatchMode(unittest.TestCase):
    def test_batch_mode_returns_single_batch(self):
        def dedup(batch):
            seen, rows = set(), []
            for r in batch.rows:
                if r["v"] not in seen:
                    seen.add(r["v"])
                    rows.append(r)
            return Batch(rows=rows)

        p = Processor(dedup, mode="batch")
        port, batch = _run(p, Batch(rows=[{"v": 1}, {"v": 1}, {"v": 2}]))[0]
        self.assertEqual([r["v"] for r in batch.rows], [1, 2])

    def test_batch_mode_returning_none_yields_nothing(self):
        p = Processor(lambda batch: None, mode="batch")
        self.assertEqual(_run(p, Batch(rows=[{"v": 1}])), [])

    def test_batch_mode_returning_iterable_of_batches(self):
        p = Processor(
            lambda batch: [Batch(rows=[r]) for r in batch.rows], mode="batch"
        )
        out = _run(p, Batch(rows=[{"v": 1}, {"v": 2}]))
        self.assertEqual(len(out), 2)
        self.assertTrue(all(port == Processor.DEFAULT_PORT for port, _ in out))


if __name__ == "__main__":
    unittest.main()
