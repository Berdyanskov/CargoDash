"""Graph construction: the >> operator, Ports, Judge wiring rules."""
import unittest

from cargodash import Module, Port, Judge, Processor


class TestModuleConnection(unittest.TestCase):
    def test_rshift_returns_downstream(self):
        a, b = Module(), Module()
        self.assertIs(a >> b, b)

    def test_rshift_records_both_directions(self):
        a, b = Module(), Module()
        a >> b
        self.assertIn(b, a._downstreams[Module.DEFAULT_PORT])
        self.assertIn(a, b._upstreams)

    def test_chaining(self):
        a, b, c = Module(), Module(), Module()
        a >> b >> c
        self.assertIn(b, a._downstreams[Module.DEFAULT_PORT])
        self.assertIn(c, b._downstreams[Module.DEFAULT_PORT])

    def test_fan_out_to_multiple_downstreams(self):
        src, d1, d2 = Module(), Module(), Module()
        src >> d1
        src >> d2
        self.assertEqual(src._downstreams[Module.DEFAULT_PORT], [d1, d2])

    def test_default_name_is_class_name(self):
        self.assertEqual(Module().name, "Module")

    def test_custom_name(self):
        self.assertEqual(Module(name="loader").name, "loader")

    def test_intra_batch_workers_floored_at_one(self):
        self.assertEqual(Module(intra_batch_workers=0).intra_batch_workers, 1)
        self.assertEqual(Module(intra_batch_workers=-5).intra_batch_workers, 1)

    def test_base_process_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            next(iter(Module().process(None)))


class TestJudgePorts(unittest.TestCase):
    def test_direct_rshift_is_rejected(self):
        j = Judge(lambda r: True)
        with self.assertRaises(TypeError):
            j >> Module()

    def test_on_true_on_false_are_ports(self):
        j = Judge(lambda r: True)
        self.assertIsInstance(j.on_true, Port)
        self.assertIsInstance(j.on_false, Port)

    def test_port_connection_records_correct_branch(self):
        j = Judge(lambda r: True)
        t, f = Module(name="t"), Module(name="f")
        j.on_true >> t
        j.on_false >> f
        self.assertEqual(j._downstreams[Judge.TRUE_PORT], [t])
        self.assertEqual(j._downstreams[Judge.FALSE_PORT], [f])

    def test_port_rshift_returns_downstream(self):
        j = Judge(lambda r: True)
        m = Module()
        self.assertIs(j.on_true >> m, m)

    def test_connecting_unknown_port_raises(self):
        # A plain module has only a "default" port.
        bogus = Port(Module(), "true")
        with self.assertRaises(ValueError):
            bogus >> Module()

    def test_judge_rejects_bad_granularity(self):
        with self.assertRaises(ValueError):
            Judge(lambda r: True, granularity="weird")

    def test_processor_rejects_bad_mode(self):
        with self.assertRaises(ValueError):
            Processor(lambda r: r, mode="nonsense")


if __name__ == "__main__":
    unittest.main()
