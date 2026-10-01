# Local build evidence

Measured on 2026-10-01, Windows, Python 3.12.10, CPU only. No network, model, or GPU calls were made. Installation used pip --no-index --no-build-isolation -e . with locally available setuptools.

- pytest: 36 passed in 0.61 seconds.
- Installed ams executable, three fresh processes: fixtures --out demo, run --input demo, report --format md. Combined measured wall time: 0.643696 seconds, below the five-second limit.
- Installed ams report --format json, fresh process: 0.192432 seconds, below the five-second limit.
- Exact report totals: 200 tasks, 100 awarded, 100 unassigned, 15000 hypothetical cost cents.
- Compared all 200 winners with independently enumerated expectations: zero mismatches, zero false positives, zero missed awards.
- Five-record hand-written synthetic example: two awards, three unassigned, 300 hypothetical cents; verified by pytest.
- Corrupting an input cost changes the computed sum by exactly one cent. Corrupting expectations alone does not change computed outputs. Corrupting the saved summary does not affect recomputed reports.
- Empty input, malformed JSONL, unknown fields, duplicates, negative values, future dates, extreme strings, Unicode, Windows paths, write failures and all command help surfaces are covered.
- Repeated identical runs and Markdown/JSON reports are byte-identical. No random seed or runtime timestamp enters the output.

The figures above measure local fixture acceptance and runtime only. They do not measure real-world agent success, time saved, money saved, daily use or revenue. No real user trial data is shipped. VERDICT.md and README define the pending two-week evaluation.

Reproduce with python -m pytest -q and the README demo. The generated demo and run cache are ignored by git; regenerate rather than treating them as real data.
