"""Tests for JoinById — stateful fan-in merger."""
from __future__ import annotations
import pytest

from cargodash import (
    Batch, Schema, RawDataSource, DataOutput, Processor, Pipeline, JoinById,
)


SCHEMA = Schema.of(id=str, a=str, b=str, c=str)


def _drive(join: JoinById, rows: list[dict]) -> list[dict]:
    """Feed `rows` (as a single batch) into the join, collect emissions."""
    out_rows: list[dict] = []
    for _port, b in join.process(Batch(rows=rows, schema=SCHEMA)):
        out_rows.extend(b.rows)
    return out_rows


def test_emits_when_expected_contributions_reached():
    j = JoinById(key="id", fields=("a", "b", "c"), expected=3,
                 input_schema=SCHEMA)
    # First two contributions: nothing emitted yet.
    assert _drive(j, [{"id": "x", "a": "A", "b": "", "c": ""}]) == []
    assert _drive(j, [{"id": "x", "a": "", "b": "B", "c": ""}]) == []
    # Third contribution unlocks emission.
    out = _drive(j, [{"id": "x", "a": "", "b": "", "c": "C"}])
    assert len(out) == 1
    assert out[0]["a"] == "A"
    assert out[0]["b"] == "B"
    assert out[0]["c"] == "C"
    # Buffer drained.
    assert j.pending == 0


def test_does_not_overwrite_with_falsy_values():
    """A later contribution with an empty value must not clobber an
    earlier truthy value (otherwise reasoning models returning ``""``
    would erase the good answer)."""
    j = JoinById(key="id", fields=("a", "b"), expected=2, input_schema=SCHEMA)
    _drive(j, [{"id": "x", "a": "good", "b": "", "c": ""}])
    out = _drive(j, [{"id": "x", "a": "", "b": "ok", "c": ""}])
    assert out[0]["a"] == "good"
    assert out[0]["b"] == "ok"


def test_emits_even_when_some_fields_remain_empty():
    """Counting contributions (not truthiness): if expected reached but a
    field never got a truthy value, still emit — downstream filters /
    verifiers decide what to do with the empty field."""
    j = JoinById(key="id", fields=("a", "b", "c"), expected=3,
                 input_schema=SCHEMA)
    out = _drive(j, [
        {"id": "x", "a": "A", "b": "", "c": ""},
        {"id": "x", "a": "", "b": "B", "c": ""},
        {"id": "x", "a": "", "b": "", "c": ""},   # model gave up: empty
    ])
    assert len(out) == 1
    assert out[0]["a"] == "A"
    assert out[0]["b"] == "B"
    assert out[0]["c"] == ""


def test_interleaved_keys():
    """Multiple keys in flight at the same time must not bleed into each other."""
    j = JoinById(key="id", fields=("a", "b"), expected=2, input_schema=SCHEMA)
    out = _drive(j, [
        {"id": "x", "a": "Ax", "b": "", "c": ""},
        {"id": "y", "a": "Ay", "b": "", "c": ""},
        {"id": "x", "a": "", "b": "Bx", "c": ""},
    ])
    assert len(out) == 1
    assert out[0]["id"] == "x"
    assert j.pending == 1   # y still buffered

    out2 = _drive(j, [{"id": "y", "a": "", "b": "By", "c": ""}])
    assert len(out2) == 1 and out2[0]["id"] == "y"
    assert j.pending == 0


def test_fields_none_merges_any_truthy_field():
    """When fields=None, JoinById merges whatever truthy field is in each
    incoming row — no need to enumerate them up-front."""
    j = JoinById(key="id", fields=None, expected=2, input_schema=SCHEMA)
    out = _drive(j, [
        {"id": "x", "a": "A", "b": "", "c": ""},
        {"id": "x", "a": "", "b": "B", "c": ""},
    ])
    assert out[0]["a"] == "A"
    assert out[0]["b"] == "B"


def test_missing_key_field_raises():
    j = JoinById(key="id", fields=("a",), expected=1, input_schema=SCHEMA)
    with pytest.raises(KeyError, match="missing key field"):
        _drive(j, [{"a": "no-id-here", "b": "", "c": ""}])


def test_invalid_expected_rejected():
    with pytest.raises(ValueError):
        JoinById(key="id", expected=0)


def test_schema_mismatch_rejected():
    s1 = Schema.of(id=str, a=str)
    s2 = Schema.of(id=str, a=int)
    with pytest.raises(ValueError, match="output_schema must equal input_schema"):
        JoinById(key="id", input_schema=s1, output_schema=s2)


def test_pipeline_end_to_end_fanout_fanin(tmp_path):
    """The canonical use: source fans out to 3 Processors that each fill
    one field; JoinById recombines them; one row in, one row out."""
    in_path = tmp_path / "in.jsonl"
    out_path = tmp_path / "out.jsonl"
    in_path.write_text(
        '{"id": "r1", "a": "", "b": "", "c": ""}\n'
        '{"id": "r2", "a": "", "b": "", "c": ""}\n'
    )

    src = RawDataSource(in_path, schema=SCHEMA, batch_size=2)
    fill_a = Processor(lambda r: {**r, "a": "A"},
                       input_schema=SCHEMA, output_schema=SCHEMA, name="fill_a")
    fill_b = Processor(lambda r: {**r, "b": "B"},
                       input_schema=SCHEMA, output_schema=SCHEMA, name="fill_b")
    fill_c = Processor(lambda r: {**r, "c": "C"},
                       input_schema=SCHEMA, output_schema=SCHEMA, name="fill_c")
    join = JoinById(key="id", fields=("a", "b", "c"), expected=3,
                    input_schema=SCHEMA, name="join")
    sink = DataOutput(out_path, schema=SCHEMA)

    src >> fill_a
    src >> fill_b
    src >> fill_c
    fill_a >> join
    fill_b >> join
    fill_c >> join
    join >> sink

    Pipeline(src).run()

    import json
    out = [json.loads(l) for l in out_path.read_text().splitlines()]
    assert sorted(r["id"] for r in out) == ["r1", "r2"]
    for r in out:
        assert r["a"] == "A" and r["b"] == "B" and r["c"] == "C"
