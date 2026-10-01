"""Pure auction logic. Costs and confidence are hypothetical supplied values."""
from datetime import date
from functools import cmp_to_key


class SchemaError(ValueError):
    """A named input contract violation."""


def integer(value, field, minimum=0, maximum=10**12):
    if type(value) is not int or not minimum <= value <= maximum:
        raise SchemaError(f"{field}: expected integer in [{minimum}, {maximum}]")


def label(value, field):
    if not isinstance(value, str) or not value or len(value) > 10000:
        raise SchemaError(f"{field}: expected nonempty string of at most 10000 characters")
    if chr(0x2014) in value:
        raise SchemaError(f"{field}: forbidden punctuation U+2014")


def fields(obj, required, field):
    if not isinstance(obj, dict):
        raise SchemaError(f"{field}: expected object")
    missing, extra = set(required) - obj.keys(), obj.keys() - set(required)
    if missing or extra:
        raise SchemaError(f"{field}: missing fields {sorted(missing)}, unknown fields {sorted(extra)}")


def validate(task):
    fields(task, ['id', 'synthetic', 'as_of', 'date', 'budget_cents', 'min_confidence_bp', 'bids'], 'task')
    label(task['id'], 'id')
    if type(task['synthetic']) is not bool:
        raise SchemaError('synthetic: expected boolean')
    for key in ['date', 'as_of']:
        try:
            if not isinstance(task[key], str) or date.fromisoformat(task[key]).isoformat() != task[key]:
                raise ValueError()
        except (ValueError, TypeError):
            raise SchemaError(f'{key}: expected ISO date YYYY-MM-DD') from None
    if task['date'] > task['as_of']:
        raise SchemaError('date: future date relative to explicit as_of')
    integer(task['budget_cents'], 'budget_cents')
    integer(task['min_confidence_bp'], 'min_confidence_bp', 1, 10000)
    if not isinstance(task['bids'], list) or len(task['bids']) > 10000:
        raise SchemaError('bids: expected list of at most 10000 bids')
    seen = set()
    for bid in task['bids']:
        fields(bid, ['agent_id', 'cost_cents', 'confidence_bp'], 'bid')
        label(bid['agent_id'], 'agent_id')
        integer(bid['cost_cents'], 'cost_cents')
        integer(bid['confidence_bp'], 'confidence_bp', 1, 10000)
        if bid['agent_id'] in seen:
            raise SchemaError('agent_id: duplicate within task')
        seen.add(bid['agent_id'])


def compare(a, b):
    # Cross products avoid floating point rounding in hypothetical ratios.
    left = a['cost_cents'] * b['confidence_bp']
    right = b['cost_cents'] * a['confidence_bp']
    ka = (left, -a['confidence_bp'], a['cost_cents'], a['agent_id'])
    kb = (right, -b['confidence_bp'], b['cost_cents'], b['agent_id'])
    return (ka > kb) - (ka < kb)


def rank(task):
    validate(task)
    eligible = [b for b in task['bids'] if b['cost_cents'] <= task['budget_cents'] and b['confidence_bp'] >= task['min_confidence_bp']]
    return sorted(eligible, key=cmp_to_key(compare))


def simulate(tasks):
    seen, rows = set(), []
    for task in tasks:
        validate(task)
        if task.get('id') in seen:
            raise SchemaError('id: duplicate task')
        bids = rank(task)
        seen.add(task['id'])
        winner = bids[0] if bids else None
        rows.append(dict(task_id=task['id'], synthetic=task['synthetic'], status='awarded' if winner else 'unassigned', winner=winner, eligible_bids=len(bids)))
    rows.sort(key=lambda row: row['task_id'])
    return dict(provenance={'synthetic_records': sum(r['synthetic'] for r in rows), 'real_records': sum(not r['synthetic'] for r in rows), 'real_data_claim': 'Records labelled real are user-entered; authorship is not independently verified.'}, totals={'tasks': len(rows), 'awarded': sum(r['status'] == 'awarded' for r in rows), 'unassigned': sum(r['status'] == 'unassigned' for r in rows), 'hypothetical_cost_cents': sum(r['winner']['cost_cents'] for r in rows if r['winner'])}, rows=rows)
