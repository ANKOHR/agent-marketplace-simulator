"""Local-file CLI. JSONL permits synthetic header comments beginning with #."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, simulate, rank, validate
from .fixtures import generate
from .report import render


class InputError(ValueError):
    pass


def read_tasks(directory, sources=None):
    path = Path(directory)
    if not path.is_dir():
        raise InputError(f'MissingInput: {path}; use ams fixtures --out demo or supply an input directory')
    tasks, seen = [], set()
    unsupported = sorted(f for f in path.iterdir() if f.suffix.lower() in ['.csv', '.yaml', '.yml', '.json'] and f.name != 'expectations.json')
    if unsupported:
        raise InputError(f'SchemaError: {unsupported[0]}:1: unsupported format; use UTF-8 JSONL task records')
    for file in sorted(path.glob('*.jsonl')):
        first = len(tasks)
        for line, text in enumerate(file.read_text(encoding='utf-8-sig').splitlines(), 1):
            if not text.strip() or text.lstrip().startswith('#'):
                continue
            try:
                task = json.loads(text)
                validate(task)
                if task['id'] in seen:
                    raise SchemaError('id: duplicate task')
                seen.add(task['id'])
                tasks.append(task)
            except json.JSONDecodeError as exc:
                raise InputError(f'ParseError: {file}:{line}: {exc.msg}') from None
            except SchemaError as exc:
                raise InputError(f'SchemaError: {file}:{line}: {exc}') from None
        if sources is not None:
            records = tasks[first:]
            sources.append(dict(file=file.name, sha256=hashlib.sha256(file.read_bytes()).hexdigest(), synthetic_records=sum(t['synthetic'] for t in records), real_records=sum(not t['synthetic'] for t in records)))
    return tasks


def atomic_write(path, text):
    path = Path(path)
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=path.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(text)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Deterministic hypothetical task auctions. Example: ams fixtures --out demo')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('fixtures', help='Generate 200 labelled synthetic records', epilog='Example: ams fixtures --out demo')
    p.add_argument('--out', required=True)
    for name, help_text in [('run', 'Compute hypothetical awards'), ('bids', 'Rank eligible hypothetical bids per task'), ('validate', 'Validate schemas and duplicate IDs')]:
        p = sub.add_parser(name, help=help_text, description=help_text, epilog=f'Example: ams {name} --input demo')
        p.add_argument('--input', required=True)
        if name == 'run':
            p.add_argument('--results', default='.ams/results.json')
    p = sub.add_parser('report', help='Render results with provenance', epilog='Example: ams report --format md')
    p.add_argument('--format', choices=['md', 'json'], default='md')
    p.add_argument('--results', default='.ams/results.json')
    p.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        if args.command == 'fixtures':
            generate(args.out)
            print('Generated 200 SYNTHETIC records. Bid figures are hypothetical.')
        elif args.command in ['run', 'bids', 'validate']:
            sources = []
            tasks = read_tasks(args.input, sources)
            if args.command == 'run':
                result = simulate(tasks)
                result['sources'] = sources
                result['inputs'] = tasks
                atomic_write(args.results, render(result, 'json'))
                print(render(result, 'json'), end='')
            elif args.command == 'bids':
                print(json.dumps(dict(label='Hypothetical supplied bids; synthetic flag preserved', tasks=[dict(task_id=t['id'], synthetic=t['synthetic'], ranked_bids=rank(t)) for t in tasks]), ensure_ascii=False, sort_keys=True, indent=2))
            else:
                print(f'Validated {len(tasks)} records; {sum(t["synthetic"] for t in tasks)} synthetic. Bid figures are hypothetical.')
        else:
            path = Path(args.results)
            if not path.is_file():
                raise InputError(f'MissingInput: {path}; run ams run --input <dir> first')
            try:
                result = json.loads(path.read_text(encoding='utf-8'))
                computed = simulate(result['inputs'])
                computed['sources'] = result['sources']
                computed['inputs'] = result['inputs']
                output = render(computed, args.format)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InputError(f'ResultError: {path}: {exc}') from None
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end='')
        return 0
    except (InputError, SchemaError, OSError, UnicodeError) as exc:
        print(f'{"FileError" if isinstance(exc, OSError) else "InputError"}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
