"""Synthetic fixtures with independently enumerated, hand-computed expectations."""
import json
from pathlib import Path


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tasks = []
    for i in range(200):
        kind = i % 4
        bids = [dict(agent_id='alpha', cost_cents=100, confidence_bp=8000), dict(agent_id='beta', cost_cents=150, confidence_bp=10000)]
        if kind == 1:
            bids = [dict(agent_id='alpha', cost_cents=100, confidence_bp=5000), dict(agent_id='beta', cost_cents=200, confidence_bp=10000)]
        if kind == 2:
            bids = [dict(agent_id='alpha', cost_cents=501, confidence_bp=10000)]
        if kind == 3:
            bids = [dict(agent_id='alpha', cost_cents=100, confidence_bp=4999)]
        tasks.append(dict(id=f'task-{i:03}', synthetic=True, as_of='2026-09-30', date='2026-09-30', budget_cents=500, min_confidence_bp=5000, bids=bids))
    (out / 'tasks.jsonl').write_text('# SYNTHETIC fixture data; no real observations\n' + ''.join(json.dumps(t, ensure_ascii=False, sort_keys=True) + '\n' for t in tasks), encoding='utf-8')
    # 50 alpha wins at 100; 50 beta wins at 200 (equal ratio, higher confidence).
    # 50 over-budget and 50 below-threshold tasks have no winner.
    expected = dict(synthetic=True, totals=dict(tasks=200, awarded=100, unassigned=100, hypothetical_cost_cents=15000), winners={f'task-{i:03}': ('alpha' if i % 4 == 0 else 'beta' if i % 4 == 1 else None) for i in range(200)})
    (out / 'expectations.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (out / 'README.md').write_text('# SYNTHETIC fixtures\nsynthetic: true\nHand computation: 50 * 100 + 50 * 200 = 15000 hypothetical cents. 100 awarded, 100 unassigned. Seed: none; enumeration is fixed.\n', encoding='utf-8')
