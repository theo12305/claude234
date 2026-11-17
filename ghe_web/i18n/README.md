# i18n: languages

Texts are written in English inside `t("...")`; the English text is the key. `t()` returns it in the current
language, `fmt()` formats numbers the way the language writes them (German: 1.234,5).

| File          | What it holds                                              |
|---------------|------------------------------------------------------------|
| `__init__.py` | `t()`, `fmt()`, the current language, month names          |
| `de.py`       | the German texts, keyed by the English text (VDI 4640 terms) |

Feature packages keep their own `de.py` (e.g. `materials/de.py`). `tests/test_i18n.py` fails when a text has no
German entry, when the placeholders differ, or when an entry is no longer used.
