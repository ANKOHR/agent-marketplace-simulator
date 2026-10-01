import json
import time
from pathlib import Path
import pytest
from agent_marketplace_simulator.cli import main, read_tasks, InputError
from agent_marketplace_simulator.fixtures import generate


def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(['fixtures', '--out', 'demo']) == 0
    assert main(['run', '--input', 'demo']) == 0
    assert main(['report', '--format', 'md']) == 0
    assert time.perf_counter() - start < 5
    assert 'Data provenance: 200 synthetic' in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'empty').mkdir()
    assert main(['run', '--input', 'empty']) == 0
    assert main(['report']) == 0
    assert 'tasks: 0' in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / 'bad.jsonl').write_text('# SYNTHETIC\n{bad json}\n')
    assert main(['run', '--input', str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert 'ParseError' in err and 'bad.jsonl:2' in err and 'Traceback' not in err


def test_determinism_byte_identical(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate('demo')
    main(['run', '--input', 'demo'])
    capsys.readouterr()
    first = Path('.ams/results.json').read_bytes()
    main(['run', '--input', 'demo'])
    assert first == Path('.ams/results.json').read_bytes()
    for fmt in ['md', 'json']:
        capsys.readouterr()
        main(['report', '--format', fmt])
        a = capsys.readouterr().out
        main(['report', '--format', fmt])
        assert a == capsys.readouterr().out


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(['fixtures', '--out', 'demo']) == 0
    for cmd in ['run', 'bids', 'validate']:
        assert main([cmd, '--input', 'demo']) == 0
    for fmt in ['md', 'json']:
        assert main(['report', '--format', fmt]) == 0
    for cmd in ['fixtures', 'run', 'report', 'bids', 'validate']:
        with pytest.raises(SystemExit) as exc:
            main([cmd, '--help'])
        assert exc.value.code == 0
        assert 'Example:' in capsys.readouterr().out


def test_handles_unicode_and_long_inputs(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate('demo')
    tasks = read_tasks('demo')[:1]
    tasks[0]['id'] = '測試 café C:\\Users\\henry ' + 'a' * 9000
    Path('demo/tasks.jsonl').write_text(json.dumps(tasks[0], ensure_ascii=False) + '\n', encoding='utf-8')
    assert main(['run', '--input', 'demo']) == 0
    assert main(['report']) == 0
    assert '測試 café' in capsys.readouterr().out


def test_missing_input_and_write_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(['run', '--input', 'absent']) == 2
    assert 'MissingInput' in capsys.readouterr().err
    generate('demo')
    Path('blocked').write_text('preserve')
    assert main(['run', '--input', 'demo', '--results', 'blocked/results.json']) == 2
    assert Path('blocked').read_text() == 'preserve'
    assert 'FileError' in capsys.readouterr().err
    main(['run', '--input', 'demo'])
    Path('destination').mkdir()
    assert main(['report', '--out', 'destination']) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ['.ams', 'blocked', 'demo', 'destination']


def test_schema_error_names_file_line_field(tmp_path, capsys):
    (tmp_path / 'bad.jsonl').write_text('{"id":"x"}\n')
    assert main(['validate', '--input', str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert 'SchemaError' in err and 'bad.jsonl:1' in err and 'bids' in err


def test_report_recomputes_corrupted_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate('demo')
    assert main(['run', '--input', 'demo']) == 0
    saved = Path('.ams/results.json')
    result = json.loads(saved.read_text())
    result['totals']['hypothetical_cost_cents'] = 999999
    saved.write_text(json.dumps(result))
    capsys.readouterr()
    assert main(['report', '--format', 'json']) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['totals']['hypothetical_cost_cents'] == 15000
    assert output['sources'][0]['file'] == 'tasks.jsonl'
    assert len(output['sources'][0]['sha256']) == 64


def test_hand_written_five_record_example():
    root = Path(__file__).resolve().parents[1] / 'examples' / 'tiny'
    from agent_marketplace_simulator.core import simulate
    expected = json.loads((root / 'expectations.json').read_text())
    result = simulate(read_tasks(root))
    assert result['totals'] == expected['totals']
    assert {r['task_id']: r['winner']['agent_id'] if r['winner'] else None for r in result['rows']} == expected['winners']


def test_mixed_real_synthetic_provenance(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate('demo')
    tasks = read_tasks('demo')[:2]
    tasks[0]['synthetic'] = False
    Path('demo/tasks.jsonl').write_text(''.join(json.dumps(t) + '\n' for t in tasks))
    assert main(['run', '--input', 'demo']) == 0
    capsys.readouterr()
    assert main(['report']) == 0
    output = capsys.readouterr().out
    assert '1 synthetic fixtures; 1 records labelled real' in output
    assert 'tasks.jsonl (1 synthetic, 1 real-labelled)' in output


def test_bad_saved_results_named_error(tmp_path, capsys):
    path = tmp_path / 'result.json'
    path.write_text('{broken')
    assert main(['report', '--results', str(path)]) == 2
    assert 'ResultError' in capsys.readouterr().err


@pytest.mark.parametrize('extension', ['json', 'csv', 'yaml'])
def test_unsupported_formats_are_named(tmp_path, capsys, extension):
    path = tmp_path / ('bad.' + extension)
    path.write_text('invalid structured data')
    assert main(['validate', '--input', str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert path.name + ':1' in error and 'SchemaError' in error
