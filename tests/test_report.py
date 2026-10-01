import json
from agent_marketplace_simulator.core import simulate
from agent_marketplace_simulator.fixtures import generate
from agent_marketplace_simulator.cli import read_tasks
from agent_marketplace_simulator.report import render


def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    r = json.loads(render(simulate(read_tasks(tmp_path)), 'json'))
    e = json.loads((tmp_path / 'expectations.json').read_text())
    assert r['totals'] == e['totals']
    assert len(r['rows']) == 200


def test_report_zero_false_positives(tmp_path):
    generate(tmp_path)
    result = simulate(read_tasks(tmp_path))
    expected = json.loads((tmp_path / 'expectations.json').read_text())['winners']
    actual = {r['task_id'] for r in result['rows'] if r['winner']}
    truth = {key for key, value in expected.items() if value is not None}
    assert actual - truth == set()
    assert truth - actual == set()


def test_report_carries_provenance_banner():
    for fmt in ['md', 'json']:
        assert 'Data provenance: 0 synthetic fixtures; 0 records labelled real' in render(simulate([]), fmt)


def test_hypothetical_figures_labelled():
    for fmt in ['md', 'json']:
        output = render(simulate([]), fmt)
        assert 'hypothetical' in output
        assert 'No savings or success predictions are measured.' in output


def test_no_em_dashes_in_outputs(tmp_path):
    generate(tmp_path)
    result = simulate(read_tasks(tmp_path))
    for fmt in ['md', 'json']:
        assert chr(0x2014) not in render(result, fmt)


def test_no_em_dashes_in_project_sources():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for folder in ['agent_marketplace_simulator', 'tests', 'examples']:
        for path in (root / folder).rglob('*'):
            if path.suffix in ['.py', '.jsonl', '.json', '.md']:
                assert chr(0x2014) not in path.read_text(encoding='utf-8'), path
    for path in root.glob('*.md'):
        assert chr(0x2014) not in path.read_text(encoding='utf-8'), path
