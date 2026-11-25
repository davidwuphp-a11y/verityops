# Verify the source release

In a fresh source checkout, use Python with SQLite support. The following commands work from the checkout root and create only synthetic data.

```sh
python -B verify_manifest.py
python -B -m unittest discover -v
python -B -m unittest discover -s legacy_tests -v
python -B -m verityops
```

The first command checks the listed file contents. The next commands should print `Ran 24 tests` and `Ran 7 tests`, each followed by `OK`. The first suite contains the 23 frozen tests and a test demonstrating that a filtered ledger view can hide a second payment while its own count still agrees. The separate seven tests cover the earlier fixture and deterministic campaign.

The batch returns exit 0 when all 11 expected labels match, six original failures replay exactly and six reference replays pass. For individual replay commands, evidence files, and exit codes 0, 1 and 2, see the [quickstart](QUICKSTART.md). Run timestamps, output directories and elapsed durations vary. Compare the evidence JSON and the verdicts.

## Observed release results

A new Windows virtual environment built the wheel from a clean source copy using a local build wheelhouse and installed it offline with no runtime dependencies. The default batch and all three individual replay examples ran with the installed wheel from a directory outside the source tree. All eleven evidence objects and all eighteen generated failure replay, reference and regression objects matched the frozen synthetic run. Python 3.12.10 and SQLite 3.49.1 were exercised. Other platforms and interpreter versions remain unverified.

The optional Agent Effects Testkit comparison ran separately in an environment containing the compatible upstream dependency. Its matched assertions returned the same 11 labels. The [test result file](test-results.json) includes the individual test names, per-case outcomes and issue codes, comparison counts, and replay exit codes. All reported results use local synthetic records.
