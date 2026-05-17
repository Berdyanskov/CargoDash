"""Vote: threshold voting across multiple predicate models."""
import unittest

from cargodash import Vote


class TestVoteConstruction(unittest.TestCase):
    def test_empty_model_list_rejected(self):
        with self.assertRaises(ValueError):
            Vote([], true_num=1)

    def test_true_num_below_range_rejected(self):
        with self.assertRaises(ValueError):
            Vote([lambda r: True], true_num=0)

    def test_true_num_above_range_rejected(self):
        with self.assertRaises(ValueError):
            Vote([lambda r: True], true_num=2)


class TestVoteDecision(unittest.TestCase):
    def test_threshold_reached(self):
        models = [lambda r: True, lambda r: True, lambda r: False]
        self.assertTrue(Vote(models, true_num=2)({}))

    def test_threshold_not_reached(self):
        models = [lambda r: True, lambda r: False, lambda r: False]
        self.assertFalse(Vote(models, true_num=2)({}))

    def test_unanimous_required(self):
        self.assertTrue(Vote([lambda r: True] * 3, true_num=3)({}))
        self.assertFalse(Vote([lambda r: True, lambda r: True, lambda r: False],
                              true_num=3)({}))

    def test_short_circuits_once_threshold_met(self):
        calls = []

        def make(name, verdict):
            def model(row):
                calls.append(name)
                return verdict
            return model

        v = Vote([make("a", True), make("b", True), make("c", True)], true_num=2)
        self.assertTrue(v({}))
        self.assertEqual(calls, ["a", "b"])  # "c" never gets called

    def test_prompt_list_forwarded_to_models(self):
        seen = []

        def model(sample, prompt):
            seen.append(prompt)
            return True

        Vote([model], true_num=1, prompt_list=["my-prompt"])({"x": 1})
        self.assertEqual(seen, ["my-prompt"])


if __name__ == "__main__":
    unittest.main()
