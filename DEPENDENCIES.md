# Dependencies and rights

Project-owned Python source, fixture definitions, examples, original tests and documentation are distributed under [Apache License 2.0](LICENSE). The repository does not bundle a Python interpreter, SQLite binary, or third-party framework.

| Component | Use and licensing |
|---|---|
| CPython and its standard library | User-supplied runtime. Python's PSF licensing and component notices apply to the Python distribution. [Python license](https://docs.python.org/3/license.html) |
| SQLite | Accessed via Python's sqlite3 module. SQLite core is public domain. [SQLite copyright](https://www.sqlite.org/copyright.html) |
| setuptools / wheel | Build-time tools supplied by the build environment. Their distributions retain their own MIT licenses. Neither is a runtime dependency of the installed demo. |
| packaging | The offline build wheelhouse also contained packaging 26.4, distributed under Apache-2.0 OR BSD-2-Clause. It is excluded from the published source and application wheel. |
| Agent Effects Testkit | Optional comparison adapter imports a separately installed compatible agent_effects package. Upstream 0.1.0a2, commit 1dcdc3466455d70dee3d878303385ca2588e4a0a, declares Apache-2.0 and dependencies including Pydantic, Rich and Typer. The default installation does not install or distribute any of these. [Upstream source](https://github.com/eschmidt01/agent-effects-testkit/tree/1dcdc3466455d70dee3d878303385ca2588e4a0a) |

The legacy compatibility tests use the project's earlier synthetic world and campaign fixtures. Their results are kept separate from the v2 acceptance suite.
