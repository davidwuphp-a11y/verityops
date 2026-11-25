# Installation

Use Python 3.11 or later built with the standard `sqlite3` module. The default demo and tests use only the standard library. From an extracted or cloned release, `python -B -m verityops` works without a package installation or network.

To install into a fresh environment, run `python -m venv .venv` and activate it using `.venv\Scripts\Activate.ps1` in PowerShell or `. .venv/bin/activate` in a POSIX shell. Then run:

```sh
python -m pip install .
python -m verityops --help
```

Source installation may download the setuptools build backend. For an offline host, build a wheel first on a build machine with setuptools 77+ and wheel installed:

```sh
python -m pip wheel --no-build-isolation --no-deps --wheel-dir dist .
```

Copy the wheel to the offline host, activate its fresh environment and install with `python -m pip install --no-index --no-deps dist/verityops-0.1.0-py3-none-any.whl`. Run from a writable working directory. Evidence is stored under its `runs/` folder. The installed console command `verityops` is equivalent to `python -m verityops`.
