"""What the parts of the page share while it is drawn, top to bottom: the language, the mode, the project the widgets
start from, the input steps and, once the inputs are read, the inputs themselves."""
from __future__ import annotations

from dataclasses import dataclass, field

from ghe_web.inputs import SectionInput


@dataclass
class Page:
    lang: str  # "en" or "de"
    ui_mode: str  # "simple" or "expert"
    gen: int  # generation of the widgets: loading a project rebuilds every widget (their keys start with it)
    project_name: str  # the name the widgets start from
    start: dict[str, SectionInput]  # the inputs the widgets start from: the defaults or a loaded project
    system: str  # heat source: "closed" (borehole heat exchangers) or "open" (groundwater wells)
    steps: dict[str, str]  # step id ("site_plan", "Site", ..., "results") -> tab label in the current language
    menu: object = None  # the ☰ popover of the app bar
    brand_slot: object = None  # the name and subtitle in the app bar
    name: str = ""  # project name as entered in the menu
    save_slot: object = None  # where "Save project" goes once the inputs are read
    share_slot: object = None  # where the share link goes once the inputs are read
    calc_slot: object = None  # the calculate bar at the bottom of the screen
    step_names: list[str] = field(default_factory=list)  # tab labels in page order
    step_tabs: dict[str, object] = field(default_factory=dict)  # tab label -> tab
    inputs: dict[str, SectionInput] = field(default_factory=dict)  # what the user entered, section by section
    notes: dict[str, object] = field(default_factory=dict)  # per section: room for notes that need other sections
    section_step: dict[str, str] = field(default_factory=dict)  # section key -> tab label it is shown in
    pending_drawings: list = field(default_factory=list)  # (where, section, variant), drawn once all are read
    typical_cards: list = field(default_factory=list)  # (where, sections): Simple's "Typical values" summary
    errors: dict[str, list[str]] = field(default_factory=dict)  # input errors per section
    cross: dict[str, list[str]] = field(default_factory=dict)  # notes that involve several sections
    current_json: str = ""  # the inputs as a project file (what a calculation is cached on)
    address: str = ""  # the address of the site plan (saved with the project)
    plugins: dict = field(default_factory=dict)  # settings of the result views (saved with the project)

    @property
    def simple(self) -> bool:
        return self.ui_mode != "expert"

    def step(self, key: str) -> str | None:
        """The tab label of a step id, or None when this heat source or mode has no such step."""
        return self.steps.get(key)
