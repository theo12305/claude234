"""Importing this package registers every built-in section.

To add a new topic: create a module next to these, define a Section,
call ``register(...)`` and import the module below.
"""
from . import ground, borefield, pipe, fluid, flow, load, limits  # noqa: F401
from .base import Property, Section, SectionInput, Variant
from .registry import get, register, sections

__all__ = ["Property", "Section", "SectionInput", "Variant", "get", "register", "sections"]
