"""The calculation button and the results of groundwater wells on the page (Streamlit)."""
from __future__ import annotations

import html
import io
from typing import Callable

import pandas as pd
import streamlit as st

from .. import checks as ghe_checks
from .. import i18n, model
from .. import ui
from ..i18n import fmt, t
from ..properties import SectionInput
from . import checks, design, plots, report, sources

VIEWS = {"overview": "Overview", "hydraulics": "Hydraulics", "temperatures": "Temperatures", "map": "Site map",
         "construction": "Well construction", "energy": "Water and energy", "checks": "Design check",
         "export": "Export"}
ICONS = {checks.PROBLEM: ":red[:material/cancel:]", checks.WARNING: ":orange[:material/warning:]",
         checks.FINE: ":green[:material/check_circle:]"}


@st.cache_resource(max_entries=16, show_spinner=False)
def cached_design(project_json: str) -> design.Design:
    return design.size(model.from_json(project_json)[1])


def _chart(c) -> None:
    ui.show_chart(c)


def _key_table(rows: list[tuple[str, str, str]]) -> None:
    body = "".join(
        f"<tr><td>{html.escape(label)}<div class='note'>{html.escape(note)}</div></td>"
        f"<td class='val'>{html.escape(value)}</td></tr>" for label, value, note in rows)
    st.markdown(f"<table class='keys'>{body}</table>", unsafe_allow_html=True)


def _all_checks(inputs: dict[str, SectionInput], errors: dict, current_json: str) -> list[ghe_checks.Check]:
    found = checks.input_checks(inputs)
    if not errors and st.session_state.get("result_json") == current_json:
        found += checks.result_checks(cached_design(current_json), inputs)
    order = {checks.PROBLEM: 0, checks.WARNING: 1, checks.FINE: 2}
    return sorted(found, key=lambda c: order[c.level])


def page(inputs: dict[str, SectionInput], errors: dict, current_json: str, name: str, lang: str, calc_slot,
         results_tab, step_of: Callable[[str], str], goto: Callable[[str], None]) -> None:
    """Sidebar calculation and the results tab. ``step_of`` gives the tab label of a section, ``goto`` opens it."""
    found = _all_checks(inputs, errors, current_json)
    checking = inputs["wells"].variant == "check"
    action = t("Check the wells") if checking else t("Size the wells")

    def calculate() -> None:
        with st.spinner(t("Calculating the wells and tracing the flow paths...")):
            try:
                cached_design(current_json)
            except Exception as exc:
                st.session_state.pop("result_json", None)
                st.session_state.calc_error = str(exc)
            else:
                st.session_state.result_json = current_json
                st.session_state.pop("calc_error", None)
            st.session_state.goto_results = True
        st.rerun()

    if st.session_state.pop("calc_requested", False):  # the button at the end of the last input step
        if errors:
            goto(next(iter(errors)))
            st.rerun()
        calculate()

    d_last = None
    if "result_json" in st.session_state:
        try:
            d_last = cached_design(st.session_state.result_json)
        except Exception:  # a result of the other heat source, or from an older version
            st.session_state.pop("result_json")
    with calc_slot:
        n = ghe_checks.counts(found)
        with st.container(width="stretch"):
            if errors:
                ui.calc_status("bad", t("{n} input(s) need attention", n=sum(len(m) for m in errors.values())),
                               "; ".join(f"{step_of(k)}: {t(model.properties.get(k).label)}" for k in errors))
            elif "calc_error" in st.session_state:
                ui.calc_status("bad", t("The calculation failed"), t("Details in 📊 Results."))
            elif d_last is not None:
                last = t("{p} + {i} wells, {d:g} m apart", p=d_last.n_production, i=d_last.n_injection,
                         d=d_last.distance) + ", " + t("{q:.1f} m³/h at peak", q=d_last.q_peak * 3600)
                if st.session_state.result_json != current_json:
                    ui.calc_status("warn", t("Inputs changed – results out of date"), t("Last result: {x}", x=last))
                else:
                    ui.calc_status("ok", t("Result up to date"), last)
            else:
                ui.calc_status("grey", t("Not calculated yet"))
        if errors:
            st.button(t("Show"), on_click=goto, args=(next(iter(errors)),), key="calc_goto_error",
                      icon=":material/arrow_upward:")
        check_label = " · ".join(x for x in (
            t("{n} problem(s)", n=n[checks.PROBLEM]) if n[checks.PROBLEM] else "",
            t("{n} warning(s)", n=n[checks.WARNING]) if n[checks.WARNING] else "") if x) or t("Design check")
        st.button(check_label, key="open_checks", help=t("Open the design check"),
                  on_click=lambda: st.session_state.update(goto_results=True, well_view_id="checks"),
                  icon=":material/error:" if n[checks.PROBLEM] else ":material/warning:" if n[checks.WARNING]
                  else ":material/fact_check:")
        if st.button(action, type="primary", disabled=bool(errors), icon=":material/play_arrow:", key="calc_go"):
            calculate()

    with results_tab:
        if "calc_error" in st.session_state:
            st.error(t("The calculation failed: {error}", error=st.session_state.calc_error), icon=":material/error:")
        if "result_json" not in st.session_state:
            st.info(t("Fill in the inputs and press **Size the wells** in the bar at the bottom."),
                    icon=":material/info:")
            _show_checks(found, step_of, goto)
            return
        sized_json = st.session_state.result_json
        sized_inputs = model.from_json(sized_json)[1]
        d = cached_design(sized_json)
        if sized_json != current_json:
            st.warning(t("These results belong to earlier inputs. Press the button in the bar at the bottom to update "
                         "them."),
                       icon=":material/update:")
        _verdict(d, sized_inputs, found if sized_json == current_json else None)
        sources_button("results")
        view = st.selectbox(t("View"), list(VIEWS), format_func=lambda k: t(VIEWS[k]), key="well_view_id", width=320)
        aquifer = design._build(sized_inputs, "aquifer")
        limits = sized_inputs["well_limits"].values
        if view == "overview":
            _overview(d, sized_inputs)
        elif view == "hydraulics":
            _hydraulics(d, aquifer)
        elif view == "temperatures":
            _chart(plots.temperature_chart(d, limits))
            st.caption(t("Monthly average temperature of the water the production wells deliver and of the water "
                         "that goes back. A rising or falling production temperature over the years means injected "
                         "water flows back to the production wells."))
        elif view == "map":
            st.pyplot(plots.site_map(d, aquifer), width="stretch")
            st.caption(t("Seen from above, the groundwater flows from left to right. Blue lines: where the injected "
                         "water goes. Shaded: the temperature change of the yearly net heat (planar model without "
                         "heat exchange with the layers above and below, so on the safe side)."))
        elif view == "construction":
            from ..properties.ground import layered
            g = sized_inputs["ground"].values
            rows = list(g["layers"]["rows"]) if layered(g) else None
            left, right = st.columns([3, 2], gap="large")
            with left:
                st.pyplot(plots.well_section(d, aquifer, rows), width="stretch")
            with right:
                _key_table([
                    (t("Well depth"), fmt("{x:.1f} m", x=d.screen.depth), t("to the aquifer bottom")),
                    (t("Screen"), fmt("{a:.1f} – {b:.1f} m", a=d.screen.top, b=d.screen.bottom),
                     t("{x:.1f} m long", x=d.screen.length)),
                    (t("Drilling diameter"), fmt("{x:.0f} mm", x=sized_inputs["wells"].values["d_bore_mm"]),
                     t("with gravel pack")),
                    (t("Screen diameter"), fmt("DN {x:.0f}", x=sized_inputs["wells"].values["dn_mm"]), ""),
                    (t("Pump depth"), fmt("{x:.1f} m", x=d.pump_depth),
                     t("2 m below the lowest water level")),
                ])
                st.caption(t("Seal the annulus above the aquifer (clay or cement) so no surface water gets down, and "
                             "keep the injection pipe below the water level so no air gets in."))
        elif view == "energy":
            _energy(d)
        elif view == "checks":
            _show_checks(found, step_of, goto)
        else:
            _export(d, sized_inputs, name, lang)


def sources_button(where: str) -> None:
    """A popover with what each part of the calculation is based on, and the literature."""
    box = st.expander(t("Calculation sources"), icon=":material/menu_book:") if where == "menu" else \
        st.popover(t("Calculation sources"), icon=":material/menu_book:")
    with box:
        st.markdown(t("**What the well calculation is based on**"))
        st.caption(t("GHEtool has no open-loop model; these methods are written for this tool and tested against the "
                     "textbook results."))
        st.markdown(sources.markdown())


def _verdict(d: design.Design, inputs, found: list | None = None) -> None:
    """The answer first: a card with the wells and the design check (all checks when the result belongs to the current
    inputs, else those of the result), then the key figures as tiles."""
    found = found if found is not None else checks.result_checks(d, inputs)
    problems = [c for c in found if c.level == checks.PROBLEM]
    warnings = [c for c in found if c.level == checks.WARNING]
    sub = t("{p} production and {i} injection well(s), {d:g} m apart, {q:.1f} m³/h at peak, {depth:.0f} m deep.",
            p=d.n_production, i=d.n_injection, d=d.distance, q=d.q_peak * 3600, depth=d.screen.depth)
    if problems:
        sub += " " + t("{n} problem(s): see the design check.", n=len(problems))
    chip_items = [("bad", t("{n} problem(s)", n=len(problems)))] if problems else []
    if warnings:
        chip_items.append(("warn", t("{n} warning(s)", n=len(warnings))))
    chip_items.append(("ok", t("{n} fine", n=len(found) - len(problems) - len(warnings))))
    ui.answer_card(not problems, t("Answer"), t("{p} + {i} wells, {d:g} m apart", p=d.n_production, i=d.n_injection,
                                                d=d.distance), sub, chip_items)
    ui.tiles([
        ("💧 " + t("Peak flow"), fmt("{x:.1f} m³/h", x=d.q_peak * 3600), fmt("{x:.1f} l/s", x=d.q_peak * 1000), ""),
        ("Σ " + t("Water per year"), fmt("{x:,.0f} m³", x=d.volume_year), "", ""),
        ("⬇️ " + t("Drawdown"), fmt("{x:.1f} m", x=d.peak.drawdown), t("of {x:.1f} m", x=d.drawdown_allowed), ""),
        ("⬆️ " + t("Rise in the injection well"), fmt("{x:.1f} m", x=d.peak.rise), t("of {x:.1f} m", x=d.rise_allowed),
         ""),
        ("❄️ " + t("Lowest production temperature"), fmt("{x:.1f} °C", x=d.t_production_min),
         t("{x:+.2f} K over the period", x=-d.drift if d.t_production_min < d.t_groundwater else d.drift), "cold"),
    ])


def _overview(d: design.Design, inputs) -> None:
    groups = report.key_groups(d, inputs)
    cols = st.columns(2, gap="large")
    for i, (group, rows) in enumerate(groups.items()):
        with cols[i % 2], st.container(border=True):
            st.markdown(f"**{group}**")
            _key_table(rows)
    if d.tried:
        with st.expander(t("How the distance was found"), icon=":material/route:"):
            table = pd.DataFrame(d.tried).rename(columns={"distance": t("Distance [m]"),
                                                          "production": t("Production wells"),
                                                          "injection": t("Injection wells"), "result": t("Result")})
            st.dataframe(table, hide_index=True, width="stretch")
            st.caption(t("Each distance gets the fewest wells that keep the water levels and the entrance velocity "
                         "within the limits; the first distance where the production temperature also stays within "
                         "the limit wins."))


def _hydraulics(d: design.Design, aquifer: dict) -> None:
    c = st.columns(4)
    c[0].metric(t("Transmissivity"), fmt("{x:.1e} m²/s", x=aquifer["kf"] * aquifer["thickness"]))
    c[1].metric(t("Drawdown at peak"), fmt("{x:.2f} m", x=d.peak.drawdown),
                t("well loss {x:.2f} m", x=d.peak.well_loss_production), delta_color="off", delta_arrow="off")
    c[2].metric(t("Rise at peak"), fmt("{x:.2f} m", x=d.peak.rise), t("incl. clogging reserve"), delta_color="off",
                delta_arrow="off")
    c[3].metric(t("Drawdown on average"), fmt("{x:.2f} m", x=d.mean.drawdown))
    _chart(plots.drawdown_profile(d, aquifer))
    st.caption(t("Steady state of the pumped and injected water (Thiem, summed over all wells), without the well "
                 "losses. Unconfined aquifers are corrected for the changing water column (Dupuit-Jacob)."))


def _energy(d: design.Design) -> None:
    _chart(plots.monthly_chart(d))
    m = d.monthly.copy()
    m["month"] = list(i18n.months())
    m = m.rename(columns={"month": t("Month"), "extraction_kwh": t("Extracted [kWh]"),
                          "injection_kwh": t("Injected [kWh]"), "volume_m3": t("Water [m³]"),
                          "spread_k": t("Mean change at injection [K]"), "pump_kwh": t("Pump [kWh]")})
    st.dataframe(m.round(2), hide_index=True, width="stretch")
    if d.hp_electricity_year is not None:
        c = st.columns(3)
        c[0].metric(t("Heat pump electricity"), fmt("{x:,.0f} kWh/yr", x=d.hp_electricity_year))
        c[1].metric(t("Well pump electricity"), fmt("{x:,.0f} kWh/yr", x=d.pump_energy_year))
        c[2].metric(t("Seasonal performance factor"), fmt("{x:.2f}", x=d.spf or 0))


def _show_checks(found, step_of, goto) -> None:
    st.markdown(t("**Design check: {summary}**", summary=ghe_checks.summary(found)))
    for i, check in enumerate(found):
        with st.container(border=True):
            text_col, button_col = st.columns([4, 1.6], vertical_alignment="center")
            text_col.markdown(f"{ICONS[check.level]} **{check.title}**  \n{check.detail}")
            if check.section and check.level != checks.FINE:
                button_col.button(t("Go to {step}", step=step_of(check.section)), key=f"wcheck.goto.{i}",
                                  width="stretch", on_click=lambda s=check.section: goto(s))


def _export(d: design.Design, inputs, name: str, lang: str) -> None:
    st.markdown(t("**Downloads**"))
    base = name.strip() or "wells"
    c1, c2 = st.columns(2)
    c1.download_button(t("Excel workbook"), lambda: i18n.call_in(lang, report.workbook, d, inputs),
                       f"{base}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       width="stretch", icon=":material/table:")
    c2.download_button(t("PDF report"), lambda: i18n.call_in(lang, report.pdf, d, inputs, name),
                       f"{base}.pdf", "application/pdf", width="stretch", icon=":material/picture_as_pdf:")
    st.caption(t("The workbook has the summary, the monthly water and energy and the temperatures of every month; "
                 "the report adds the site map and the well construction."))
