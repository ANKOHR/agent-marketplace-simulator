"""Provenance and hypothetical labels are mandatory on both report surfaces."""
import json


def render(result, format='md'):
    p = result['provenance']
    banner = f"Data provenance: {p['synthetic_records']} synthetic fixtures; {p['real_records']} records labelled real (user-entered, unverified). Costs and confidence are hypothetical supplied bids, not measured outcomes. No savings or success predictions are measured."
    sources = result.get('sources', [])
    if sources:
        banner += ' Input files: ' + '; '.join(f"{item['file']} ({item['synthetic_records']} synthetic, {item['real_records']} real-labelled)" for item in sources) + '.'
    if format == 'json':
        return json.dumps({**result, 'banner': banner}, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    t = result['totals']
    lines = ['# Agent Marketplace Simulator', '', banner, '', *[f'{key}: {value}' for key, value in t.items()], '', '| Task | Status | Winner | Hypothetical cost cents |', '| :--- | :--- | :--- | ---: |']
    for row in result['rows']:
        winner = row['winner']
        escape = lambda value: str(value).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')
        lines.append(f"| {escape(row['task_id'])} | {row['status']} | {escape(winner['agent_id']) if winner else ''} | {winner['cost_cents'] if winner else 0} |")
    return '\n'.join(lines) + '\n'
