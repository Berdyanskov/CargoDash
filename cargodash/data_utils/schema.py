"""Schema: a lightweight name -> python-type mapping with equality."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Schema:
    fields: tuple[tuple[str, type], ...]

    @classmethod
    def of(cls, **fields: type) -> "Schema":
        return cls(tuple(sorted(fields.items())))

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.fields)

    def validate_row(self, row: Mapping) -> None:
        for name, typ in self.fields:
            if name not in row:
                raise ValueError(f"row missing field '{name}'")
            if not isinstance(row[name], typ):
                raise TypeError(
                    f"field '{name}': expected {typ.__name__}, got {type(row[name]).__name__}"
                )

    def is_compatible_with(self, other: "Schema") -> bool:
        # Strict equality for now; relax to subset/coercion later if useful.
        return self == other
