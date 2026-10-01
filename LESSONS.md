# Lessons for KOML

Domain lesson: cheapest bids do not necessarily win when confidence is included. The equal-ratio planted case chooses the higher-confidence agent at a higher hypothetical price. Confidence remains an assertion; ranking does not establish actual task success.

Validated assumption: integer cost/confidence comparisons and explicit tie-breaks produce repeatable allocations, reconcile exact cents, and identify every planted winner with zero false positives. Broken development assumption: a JSON report containing a banner could be rendered again without handling the existing banner key. The end-to-end CLI smoke test exposed that collision; rendering now replaces the banner explicitly.

Evidence-based build improvement: saved reports recompute explicit input snapshots, and include per-file provenance and hashes. This prevents trusting a stale or modified cached summary. A regression test verifies summary corruption cannot change the report's computed totals. This local improvement is distinct from the prospective two-week real-use hook.

Operating rule: hand-compute expectations independently, test the installed CLI including report re-rendering, and label asserted bid values as hypothetical even when the source records are real.
