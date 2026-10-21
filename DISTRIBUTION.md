# Checking a distribution

[Version française](DISTRIBUTION.fr.md)

Build the source archive and the wheel, then check their metadata:

```bash
python -m pip install build twine
python -m build
python -m twine check --strict dist/*
```

Install the single wheel from `dist/` in a fresh virtual environment. Run this from that environment:

```bash
python tools/check_distribution.py
```

The check runs `component-manifest-lint --help` and the module entry point from a temporary directory. It removes `PYTHONPATH`; the module runs with Python isolated mode. A source checkout cannot satisfy these imports. The included valid fixture also exercises packaged runtime resources.

The distribution workflow repeats this on Ubuntu and Windows with Python 3.12. The existing test workflow remains responsible for the supported Python matrix. This job does not publish to PyPI or create releases.

Before publishing, verify the package name and ownership, review the included files and license, select a tested commit and version, and configure the intended publisher. Build tools need network access; this does not change the runtime network behaviour.

References: [Python packaging flow](https://packaging.python.org/en/latest/flow/), [distribution checks](https://packaging.python.org/en/latest/discussions/setup-py-deprecated/).

---

<div align="center">
  <img src="https://raw.githubusercontent.com/jihedbfr-art/jihedbfr-art/main/assets/brand/jihedailabs-logo.svg" alt="JihedAiLabs" width="120"/>
  <br/>
  <sub>A <a href="https://github.com/jihedbfr-art"><b>JihedAiLabs</b></a> project</sub>
</div>
