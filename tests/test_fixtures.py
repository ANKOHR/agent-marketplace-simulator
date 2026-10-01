import json
from agent_marketplace_simulator.fixtures import generate
from agent_marketplace_simulator.cli import read_tasks
from agent_marketplace_simulator.core import simulate


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / 'tasks.jsonl').read_text().startswith('# SYNTHETIC')
    assert all(t['synthetic'] is True for t in read_tasks(tmp_path))
    assert json.loads((tmp_path / 'expectations.json').read_text())['synthetic'] is True
    assert 'synthetic: true' in (tmp_path / 'README.md').read_text()


def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    expected = json.loads((tmp_path / 'expectations.json').read_text())
    result = simulate(read_tasks(tmp_path))
    assert expected['totals'] == dict(tasks=200, awarded=100, unassigned=100, hypothetical_cost_cents=15000)
    assert result['totals'] == expected['totals']
    assert {r['task_id']: r['winner']['agent_id'] if r['winner'] else None for r in result['rows']} == expected['winners']


def test_corrupted_fixture_changes_computed_figures(tmp_path):
    generate(tmp_path)
    tasks = read_tasks(tmp_path)
    tasks[0]['bids'][0]['cost_cents'] = 99
    assert simulate(tasks)['totals']['hypothetical_cost_cents'] == 14999
    # The expectations file is never consulted by the engine.
    (tmp_path / 'expectations.json').write_text('{}')
    assert simulate(read_tasks(tmp_path))['totals']['hypothetical_cost_cents'] == 15000
