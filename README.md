# Agent Marketplace Simulator

A CPU-only Python CLI that assigns tasks using explicitly supplied cost and confidence bids. No model calls, network calls, GPU libraries, or database. Python 3.10 or newer, no runtime dependencies.

## Hypothesis and acceptance

A deterministic auction with labelled inputs and exact arithmetic can make task allocation auditable. Acceptance: all 200 planted records reconcile with independent hand-computed expectations, all winners found, zero false positives, and the full demo takes under five seconds locally. These checks establish correctness on fixtures, not agent reliability in production. Local measurements are in EVIDENCE.md.

## Quickstart

Install from this repo without accessing a package index (setuptools 68+ must already be available):

```powershell
python -m pip install --no-index --no-build-isolation -e .
ams fixtures --out demo
ams run --input demo
ams report --format md
python -m pytest -q
```

On Windows, if pip warns that its Scripts directory is absent from PATH, add the exact directory printed by pip to the current session's PATH, or use `python -m agent_marketplace_simulator.cli` in place of `ams`. pytest is a development requirement and must be installed locally. No packages are downloaded by this project.

The smallest hand-written five-record example ships at `examples/tiny`:

```powershell
ams run --input examples/tiny
ams report --format md
```

Its ground truth is two awards, three unassigned tasks, and 300 hypothetical cents. The generated demo contains 200 records. Both are synthetic.

## Input reference and auction rules

Use a dedicated directory containing UTF-8 `*.jsonl` files. Each nonblank, non-comment line is one task object. Lines beginning with `#` are comments. All task files are read in filename order. `expectations.json` and Markdown notes are metadata, never auction inputs. CSV, YAML and other JSON files are rejected with a named unsupported-format error instead of being silently interpreted. Other file extensions are not input files.

```json
{"id":"review-1","synthetic":false,"date":"2026-09-30","as_of":"2026-09-30","budget_cents":500,"min_confidence_bp":5000,"bids":[{"agent_id":"henry-agent","cost_cents":100,"confidence_bp":8000}]}
```

This example is illustrative, not Henry's actual data. Set `synthetic:false` only for records Henry enters from his own real operation. That flag is a user claim, not an independently verified source. Trial data should stay local and must not be committed.

| Field | Contract |
| :--- | :--- |
| id | Unique across all task files; nonempty string, at most 10,000 characters |
| synthetic | Required boolean, true for fixtures and illustrative examples |
| date, as_of | Exact ISO YYYY-MM-DD dates; date cannot exceed explicit as_of |
| budget_cents | Integer 0 through 1,000,000,000,000, in a single consistent currency chosen by the user |
| min_confidence_bp | Integer 1 through 10,000; 8000 means an asserted 80 percent confidence |
| bids | List of at most 10,000 bid objects; empty is allowed |
| agent_id | Same string limits as id; unique within a task; may bid on multiple tasks |
| cost_cents | Integer 0 through 1,000,000,000,000, hypothetical proposed price |
| confidence_bp | Integer 1 through 10,000, hypothetical asserted confidence |

Unknown or missing fields, negative values, floats, booleans in numeric fields, duplicate IDs, invalid dates, and oversized strings are rejected. Unicode and Windows path strings are preserved. U+2014 punctuation is rejected in IDs to satisfy the output punctuation contract. Entire runs fail on invalid records; none are silently dropped. Future dates are relative to the supplied as_of, not a changing system clock.

A bid is eligible when cost is no higher than budget and confidence is no lower than the task threshold. Choose the smallest cost/confidence ratio, comparing integer cross products without floating point. Ties prefer higher confidence, then lower cost, then lexicographically smaller agent ID. Zero cost is allowed. No eligible bids means unassigned. Tasks are independent: agents have no capacity constraints. There is no learned bidding strategy or inferred probability. Totals count tasks and sum winning hypothetical costs exactly.

## Subcommand catalogue

Every subcommand provides `--help` with an example.

| Command | Example and purpose |
| :--- | :--- |
| fixtures | `ams fixtures --out demo`: generate 200 synthetic records and independent expectations; use a dedicated output directory |
| validate | `ams validate --input demo`: check all schemas and duplicate IDs without saving a run |
| bids | `ams bids --input demo`: show eligible bids in deterministic rank order with synthetic flags |
| run | `ams run --input demo --results .ams/results.json`: calculate and atomically save results plus explicit inputs and source hashes |
| report | `ams report --format json --out report.json`: recompute stored inputs and render with provenance; md is also supported |

`run` defaults to `.ams/results.json`; report reads that path by default. Use `--results <path>` on both commands to keep multiple runs. A report describes a saved input snapshot, not edits to the input directory made afterwards. Run again to include edits. Output contains no timestamps or variable runtime fields. Same inputs give byte-identical output, with fixed enumeration and no random seed needed.

## Architecture

```text
UTF-8 JSONL files -> cli.read_tasks -> core.validate -> core.rank
                                                     -> core.simulate
                                                        -> saved input snapshot + results
                                                        -> report.render -> Markdown / JSON
fixtures.generate -> labelled records + independent expectations
pytest -> acceptance, adversarial, provenance and determinism checks
```

Core functions perform no I/O. Results include each task ID, synthetic flag, winner, status and eligible bid count. CLI reports name each input file and its real/synthetic counts; JSON also includes SHA-256 source hashes and all input bids for traceability. Both formats carry the provenance banner. Reports recompute the snapshot rather than trusting saved summary figures.

## Honesty boundary

Every cost and confidence is a hypothetical supplied bid, including bids entered from a real operation. It is not a measured payment, calibrated success probability or forecast. Real-labelled records and synthetic fixtures are separately counted. The tool computes allocations only from its inputs and never discovers or estimates anything beyond them. It does not report time saved, money saved, actual success, revenue, or baseline improvements. Local elapsed demo time is a measured performance check, not a savings claim. No real Henry data is shipped.

Every generated fixture file identifies synthetic provenance: JSONL has a header comment and `synthetic:true` per record; JSON expectations have `synthetic:true` (JSON does not support comments); Markdown has a synthetic heading and `synthetic: true`. Examples use the same policy. Fixture expectations are not read by the engine. Fifty alpha wins at 100 cents plus fifty beta wins at 200 cents total 15,000 hypothetical cents. Fifty over-budget and fifty below-threshold tasks are unassigned. Changing inputs changes output; changing expectations alone does not.

## Failure modes

- Malformed JSONL: ParseError names the file and one-based line, exits 2 without traceback.
- Missing directory or results: MissingInput with a usage hint, exits 2.
- Schema drift or adversarial value: SchemaError names file, line and offending field, exits 2.
- Unsupported structured input format: SchemaError names file and line 1 with a JSONL conversion hint.
- Unreadable input or unwritable report: FileError names the operating system failure, exits 2. Atomic same-directory replacement preserves an existing result and removes temporary files on failure.
- Corrupt saved results: ResultError names the result file. Reports recompute from the saved inputs.
- Poor confidence calibration or unrealistic bids: accepted as user assertions and labelled hypothetical; the simulator cannot measure their truth.

## Evidence-based improvement and verdict

The two-week real-use window has not started. Do not invent a completed verdict or real-use results. Start the window on the first real run, record the date and local trial findings in an uncommitted file. Measure task-award error rate against a hand-checked sample: mismatched winner or unassigned decision divided by checked tasks. Record sample size, reference decisions, observed decisions, runs used and use days. An empty sample is unmeasured, not zero error.

After 14 days, if error exceeds 10 percent, fix the most frequent failure cause and retest, or kill with the reason. If unused, kill with the reason. Record the evidence and choose expand if daily use or revenue warrants it; integrate if overlap with a sibling dominates; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if unused or acceptance cannot be met. VERDICT.md records the current evidence status. The prospective metric and decision rule are the single improvement hook, not a claim of improvement already measured.

Publishing is a separate verification step. This build does not publish or access GitHub.
