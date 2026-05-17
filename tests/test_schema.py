"""Schema: construction, row validation, equality/compatibility."""
import unittest

import pyarrow as pa

from cargodash import Schema


class TestSchemaConstruction(unittest.TestCase):
    def test_of_with_python_types(self):
        s = Schema.of(text=str, score=int, ratio=float, ok=bool, blob=bytes)
        self.assertEqual(s.field_names, ("text", "score", "ratio", "ok", "blob"))

    def test_of_with_arrow_datatype(self):
        s = Schema.of(tags=pa.list_(pa.string()))
        self.assertEqual(s.field_names, ("tags",))

    def test_of_rejects_unmapped_python_type(self):
        with self.assertRaises(TypeError):
            Schema.of(weird=complex)

    def test_of_rejects_garbage_spec(self):
        with self.assertRaises(TypeError):
            Schema.of(bad=123)


class TestSchemaValidateRow(unittest.TestCase):
    def setUp(self):
        self.schema = Schema.of(text=str, score=int)

    def test_valid_row_passes(self):
        self.schema.validate_row({"text": "hi", "score": 3})

    def test_missing_field_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.schema.validate_row({"text": "hi"})

    def test_wrong_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.schema.validate_row({"text": "hi", "score": "not-int"})

    def test_extra_fields_are_allowed(self):
        # validate_row only checks declared fields; extras are ignored.
        self.schema.validate_row({"text": "hi", "score": 3, "extra": object()})


class TestSchemaEquality(unittest.TestCase):
    def test_equal_schemas(self):
        a = Schema.of(text=str, score=int)
        b = Schema.of(text=str, score=int)
        self.assertEqual(a, b)
        self.assertTrue(a.is_compatible_with(b))
        self.assertEqual(hash(a), hash(b))

    def test_field_order_matters(self):
        a = Schema.of(text=str, score=int)
        b = Schema.of(score=int, text=str)
        self.assertNotEqual(a, b)
        self.assertFalse(a.is_compatible_with(b))

    def test_unequal_to_non_schema(self):
        self.assertNotEqual(Schema.of(text=str), "not a schema")

    def test_hashable_and_dedups_in_set(self):
        bag = {Schema.of(text=str), Schema.of(text=str)}
        self.assertEqual(len(bag), 1)


if __name__ == "__main__":
    unittest.main()
