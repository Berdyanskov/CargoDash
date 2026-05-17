"""Judge: routing a batch onto the true / false ports."""
import unittest

from cargodash import Judge, Batch


def _run(judge, batch):
    return list(judge.process(batch))


class TestJudgeSampleGranularity(unittest.TestCase):
    def test_splits_rows_across_both_ports(self):
        j = Judge(lambda r: r["v"] > 0)
        out = dict(_run(j, Batch(rows=[{"v": -1}, {"v": 1}, {"v": 2}])))
        self.assertEqual([r["v"] for r in out[Judge.TRUE_PORT].rows], [1, 2])
        self.assertEqual([r["v"] for r in out[Judge.FALSE_PORT].rows], [-1])

    def test_all_true_emits_only_true_port(self):
        j = Judge(lambda r: True)
        ports = [p for p, _ in _run(j, Batch(rows=[{"v": 1}, {"v": 2}]))]
        self.assertEqual(ports, [Judge.TRUE_PORT])

    def test_all_false_emits_only_false_port(self):
        j = Judge(lambda r: False)
        ports = [p for p, _ in _run(j, Batch(rows=[{"v": 1}]))]
        self.assertEqual(ports, [Judge.FALSE_PORT])

    def test_intra_batch_workers_preserve_order(self):
        j = Judge(lambda r: r["v"] % 2 == 0, intra_batch_workers=4)
        out = dict(_run(j, Batch(rows=[{"v": i} for i in range(10)])))
        self.assertEqual([r["v"] for r in out[Judge.TRUE_PORT].rows], [0, 2, 4, 6, 8])
        self.assertEqual([r["v"] for r in out[Judge.FALSE_PORT].rows], [1, 3, 5, 7, 9])

    def test_batch_schema_carried_onto_branches(self):
        from cargodash import Schema
        s = Schema.of(v=int)
        j = Judge(lambda r: r["v"] > 0)
        out = dict(_run(j, Batch(rows=[{"v": 1}, {"v": -1}], schema=s)))
        self.assertEqual(out[Judge.TRUE_PORT].schema, s)
        self.assertEqual(out[Judge.FALSE_PORT].schema, s)


class TestJudgeBatchGranularity(unittest.TestCase):
    def test_whole_batch_routed_to_true(self):
        j = Judge(lambda batch: len(batch) > 1, granularity="batch")
        out = _run(j, Batch(rows=[{"v": 1}, {"v": 2}]))
        self.assertEqual(out[0][0], Judge.TRUE_PORT)

    def test_whole_batch_routed_to_false(self):
        j = Judge(lambda batch: len(batch) > 10, granularity="batch")
        out = _run(j, Batch(rows=[{"v": 1}]))
        self.assertEqual(out[0][0], Judge.FALSE_PORT)

    def test_batch_is_passed_through_untouched(self):
        j = Judge(lambda batch: True, granularity="batch")
        original = Batch(rows=[{"v": 1}, {"v": 2}])
        port, out = _run(j, original)[0]
        self.assertIs(out, original)


if __name__ == "__main__":
    unittest.main()
