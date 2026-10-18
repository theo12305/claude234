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

from ..i18n import t

# "points": a list of (x, y) borehole positions in metres.
# "hourly": {"heating": [8760 values], "cooling": [8760 values]} in kW.
# "layers": {"use": bool, "rows": [{"top", "bottom", "rock", "k_s", "C", ...}]}, depths in m below ground.
PropertyKind = Literal["float", "int", "choice", "bool", "monthly", "points", "hourly", "layers"]


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
                    errors.append(t("{label}: the {load} demand needs 8760 hourly values.", label=t(self.label),
                                    load=t(key)))
                elif min(series) < 0:
                    errors.append(t("{label}: the {load} demand cannot be negative.", label=t(self.label),
                                    load=t(key)))
            return errors
        if self.kind == "layers":
            if not isinstance(value, dict):
                return [t("{label}: not a layer table.", label=t(self.label))]
            if value.get("use"):
                from ..strata.predict import check_rows
                errors.extend(f"{t(self.label)}: {msg}" for msg in check_rows(list(value.get("rows") or [])))
            return errors
        if self.kind == "points":
            if len(value) == 0:
                errors.append(t("{label}: at least one borehole is needed.", label=t(self.label)))
            elif any(len(p) != 2 or any(not isinstance(c, (int, float)) or c != c for c in p) for p in value):
                errors.append(t("{label}: every borehole needs a numeric x and y coordinate.", label=t(self.label)))
            return errors
        values = value if self.kind == "monthly" else [value]
        if self.kind == "monthly" and len(values) != 12:
            errors.append(t("{label}: 12 monthly values are needed, found {n}.", label=t(self.label), n=len(values)))
        if self.kind == "choice" and value not in self.options:
            errors.append(t("{label}: '{value}' is not one of the options.", label=t(self.label), value=t(str(value))))
        for v in values:
            if self.min is not None and v < self.min:
                errors.append(t("{label}: {value:g} is below the minimum of {limit:g} {unit}.", label=t(self.label),
                                value=v, limit=self.min, unit=t(self.unit)).strip())
                break
            if self.max is not None and v > self.max:
                errors.append(t("{label}: {value:g} is above the maximum of {limit:g} {unit}.", label=t(self.label),
                                value=v, limit=self.max, unit=t(self.unit)).strip())
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
                errors.append(t("{label}: no value given.", label=t(p.label)))
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
