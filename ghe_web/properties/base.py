"""Building blocks for describing user inputs.

A *Property* is one input field (e.g. ground conductivity).
A *Variant* is one way of describing a topic (e.g. "constant ground temperature")
and knows how to turn its values into a GHEtool object.
A *Section* is a topic on the page (e.g. "Ground") with one or more variants.

To extend the interface you only add Properties, Variants or Sections;
the web page and the model builder pick them up automatically.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

# "points": a list of (x, y) borehole positions in metres.
# "hourly": {"heating": [8760 values], "cooling": [8760 values]} in kW.
PropertyKind = Literal["float", "int", "choice", "bool", "monthly", "points", "hourly"]


@dataclass(frozen=True)
class Property:
    key: str
    label: str
    default: Any
    unit: str = ""
    kind: PropertyKind = "float"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    options: tuple = ()
    help: str = ""
    # True for loads that should grow and shrink with the building demand (used by the sensitivity check).
    scales_with_load: bool = False

    def validate(self, value: Any) -> list[str]:
        """Return a list of human readable problems with ``value`` (empty if fine)."""
        errors = []
        if self.kind == "hourly":
            for key in ("heating", "cooling"):
                series = value.get(key) if isinstance(value, dict) else None
                if series is None or len(series) != 8760:
                    errors.append(f"{self.label}: {key} needs 8760 hourly values.")
                elif min(series) < 0:
                    errors.append(f"{self.label}: {key} demand cannot be negative.")
            return errors
        if self.kind == "points":
            if len(value) == 0:
                errors.append(f"{self.label}: at least one borehole is needed.")
            elif any(len(p) != 2 or any(not isinstance(c, (int, float)) or c != c for c in p) for p in value):
                errors.append(f"{self.label}: every borehole needs a numeric x and y.")
            return errors
        values = value if self.kind == "monthly" else [value]
        if self.kind == "monthly" and len(values) != 12:
            errors.append(f"{self.label}: expected 12 monthly values, got {len(values)}.")
        if self.kind == "choice" and value not in self.options:
            errors.append(f"{self.label}: '{value}' is not one of {list(self.options)}.")
        for v in values:
            if self.min is not None and v < self.min:
                errors.append(f"{self.label}: {v} is below the minimum of {self.min} {self.unit}.".strip())
                break
            if self.max is not None and v > self.max:
                errors.append(f"{self.label}: {v} is above the maximum of {self.max} {self.unit}.".strip())
                break
        return errors


@dataclass(frozen=True)
class PresetGroup:
    """A drop-down of named value sets, e.g. {"Granite": {"k_s": 3.4, ...}}. Picking one fills those fields."""
    label: str
    options: dict[str, dict[str, Any]]
    help: str = ""


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    properties: tuple[Property, ...]
    # Turns the values of this variant into something GHEtool understands.
    build: Callable[[dict[str, Any]], Any]
    help: str = ""
    # Checks that involve several properties; each returns an error message or None.
    checks: tuple[Callable[[dict[str, Any]], str | None], ...] = ()
    # Like checks, but only a warning: the calculation still runs.
    warnings: tuple[Callable[[dict[str, Any]], str | None], ...] = ()
    # Ready-made values the user can pick from, e.g. rock types or pipe sizes.
    presets: tuple["PresetGroup", ...] = ()

    def defaults(self) -> dict[str, Any]:
        return {p.key: p.default for p in self.properties}

    def check_warnings(self, values: dict[str, Any]) -> list[str]:
        return [msg for check in self.warnings if (msg := check(values))]

    def validate(self, values: dict[str, Any]) -> list[str]:
        errors = []
        for p in self.properties:
            if p.key not in values:
                errors.append(f"{p.label}: missing value.")
            else:
                errors.extend(p.validate(values[p.key]))
        if not errors:
            errors.extend(msg for check in self.checks if (msg := check(values)))
        return errors


@dataclass(frozen=True)
class Section:
    key: str
    label: str
    variants: tuple[Variant, ...]
    help: str = ""
    order: int = 100
    group: str = ""  # page step the section is shown in, e.g. "Site"; empty puts it under "More inputs"

    def variant(self, key: str | None = None) -> Variant:
        if key is None:
            return self.variants[0]
        for v in self.variants:
            if v.key == key:
                return v
        raise KeyError(f"Section '{self.key}' has no variant '{key}'.")


@dataclass
class SectionInput:
    """The user's choice for one section: which variant and its values."""
    variant: str
    values: dict[str, Any] = field(default_factory=dict)
