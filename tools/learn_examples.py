"""Writes ghe_web/learn/examples.json: the required length and the sensitivity of every Learn-mode parameter for the
three example projects. Run after changing the projects or the sizing:  python -m tools.learn_examples
(takes a few minutes; tests/test_learn.py checks that the stored lengths still match)."""
import json
import warnings

from ghe_web.learn import projects


def main() -> None:
    warnings.filterwarnings("ignore")
    data = {}
    for project in projects.PROJECTS:
        data[project.key] = projects.compute(project)
        print(project.key, data[project.key]["length"], flush=True)
    projects.DATA.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
