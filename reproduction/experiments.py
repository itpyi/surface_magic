"""Supplement D experiments. Circuit constructors retain their historical gates."""
from dataclasses import dataclass
import numpy as np
from simulations.offline.with_growth import preparation as grown, further_growth
from simulations.offline.without_growth import preparation as ungrown
from simulations.online import teleportation as online

@dataclass
class Case:
    metadata: dict
    circuit: object
    postselect: bool

EXPERIMENTS = ('offline-error', 'offline-t1', 'offline-t2', 'offline-maintain',
               'offline-distance', 'no-grow-error', 'no-grow-t1',
               'online', 'online-time', 'online-legacy-error', 'ts')

def cases(name, smoke=False, probabilities=None):
    ps = probabilities if probabilities is not None else (
        [1e-3] if smoke else np.linspace(1e-4, 1e-3, 10).tolist())
    base = dict(T_sc_pre=0, T_lat_surg=3, T_before_grow=1,
                T_ps_grow=2, T_maintain=0, error_rate=1e-3)
    if name.startswith('offline'):
        key, values = {
            'offline-error': ('error_rate', ps),
            'offline-t1': ('T_before_grow', [1, 2] if smoke else range(1, 10)),
            'offline-t2': ('T_ps_grow', [0, 2] if smoke else range(10)),
            'offline-maintain': ('T_maintain', [0, 1] if smoke else range(10)),
            'offline-distance': ('d2', [7, 9] if smoke else [7, 9, 11, 13, 15]),
        }[name]
        # Preserve the extra initial cycle in these historical sweeps.
        if name in ('offline-maintain', 'offline-distance'):
            base['T_sc_pre'] = 1
        for value in values:
            kw = dict(base, **{key: value})
            build = further_growth.build_circuit if name == 'offline-distance' else grown.build_circuit
            yield Case(dict(experiment=name, **kw), build(**kw), True)
    elif name.startswith('no-grow'):
        base = {k: v for k, v in base.items() if k not in ('T_ps_grow', 'T_maintain')}
        key = 'error_rate' if name == 'no-grow-error' else 'T_before_grow'
        values = ps if key == 'error_rate' else ([1, 2] if smoke else range(1, 10))
        if key != 'error_rate':
            base['T_sc_pre'] = 1
        for value in values:
            kw = dict(base, **{key: value})
            yield Case(dict(experiment=name, **kw), ungrown.build_circuit(**kw), True)
    elif name == 'online-time':
        for t in ([1, 9] if smoke else range(1, 10)):
            kw = dict(T=10, T_lat_surg=3, t_round=t, error_rate=1e-3)
            yield Case(dict(experiment=name, **kw), online.build_circuit(**kw), False)
    else:
        # Supplement D.2 has one additional pre-cycle and one post-cycle.
        # Old error sweep used T=6 instead; retain it under a distinct name.
        T = 6 if name == 'online-legacy-error' else 1
        ps = probabilities if probabilities is not None else ([1e-3] if smoke else (
            np.logspace(-6, -3, 10).tolist() if T == 6 else np.logspace(-2.5, -3, 6).tolist()))
        for p in ps:
            for stage, t in [('before', T), ('after', T + 1)]:
                kw = dict(T=T, T_lat_surg=3, t_round=t, error_rate=p)
                yield Case(dict(experiment=name, stage=stage, **kw), online.build_circuit(**kw), False)
