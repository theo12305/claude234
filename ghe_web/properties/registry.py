"""Central list of all sections shown in the interface."""
from __future__ import annotations

from .base import Section

_SECTIONS: dict[str, Section] = {}


def register(section: Section) -> Section:
    if section.key in _SECTIONS:
        raise ValueError(f"Section '{section.key}' is already registered.")
    _SECTIONS[section.key] = section
    return section


def sections(system: str | None = None) -> list[Section]:
    """All sections in page order; with ``system`` ("closed" or "open") only those that belong to it."""
    found = [s for s in _SECTIONS.values() if system is None or s.system in ("", system)]
    return sorted(found, key=lambda s: s.order)


def get(key: str) -> Section:
    return _SECTIONS[key]
