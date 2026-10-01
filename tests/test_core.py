import copy
import pytest
from agent_marketplace_simulator.core import simulate, SchemaError


def task():
    return dict(id='one', synthetic=False, date='2026-09-30', as_of='2026-09-30', budget_cents=500, min_confidence_bp=5000, bids=[dict(agent_id='a', cost_cents=100, confidence_bp=5000), dict(agent_id='b', cost_cents=200, confidence_bp=10000)])


def test_ratio_tie_prefers_confidence():
    assert simulate([task()])['rows'][0]['winner']['agent_id'] == 'b'


@pytest.mark.parametrize('field,value', [('budget_cents', -1), ('budget_cents', True), ('date', '2026-10-01'), ('id', 'x' * 10001), ('min_confidence_bp', 0), ('as_of', 'oops')])
def test_rejects_adversarial_values(field, value):
    t = task()
    t[field] = value
    with pytest.raises(SchemaError, match=field):
        simulate([t])


@pytest.mark.parametrize('field,value', [('cost_cents', -1), ('confidence_bp', 10001), ('confidence_bp', 0)])
def test_rejects_bad_bids(field, value):
    t = task()
    t['bids'][0][field] = value
    with pytest.raises(SchemaError, match=field):
        simulate([t])


def test_duplicates_and_schema_drift():
    t = task()
    with pytest.raises(SchemaError, match='duplicate task'):
        simulate([t, t])
    t['bids'].append(copy.deepcopy(t['bids'][0]))
    with pytest.raises(SchemaError, match='agent_id'):
        simulate([t])
    t = task()
    t['unknown'] = 1
    with pytest.raises(SchemaError, match='unknown'):
        simulate([t])


def test_zero_cost_and_agent_tie():
    t = task()
    t['bids'] = [dict(agent_id=a, cost_cents=0, confidence_bp=5000) for a in ['z', 'a']]
    assert simulate([t])['rows'][0]['winner']['agent_id'] == 'a'
