"""Central list of all sections shown in the interface."""
from __future__ import annotations

from .base import Section

_SECTIONS: dict[str, Section] = {}


def register(section: Section) -> Section:
    if section.key in _SECTIONS:
        raise ValueError(f"Section '{section.key}' is already registered.")
    _SECTIONS[section.key] = section
    return section


def sections() -> list[Section]:
    return sorted(_SECTIONS.values(), key=lambda s: s.order)


def get(key: str) -> Section:
    return _SECTIONS[key]
