"""Independent checks for the scientific paths affected by organization."""
import itertools
import unittest
from unittest.mock import patch
import numpy as np
import sinter
import stim
from reproduction.ip import IPDecoder, matrices
from reproduction.experiments import cases
from simulations.st_comparison import statevector as ts

class Invariants(unittest.TestCase):
    def test_circuit_noiseless(self):
        for name in ['offline-t1', 'offline-t2', 'offline-distance', 'offline-maintain',
                     'no-grow-t1', 'online', 'online-legacy-error', 'online-time']:
            for case in cases(name, smoke=True):
                circuit = case.circuit.without_noise()
                circuit.detector_error_model()
                det, obs = circuit.compile_detector_sampler(seed=17).sample(32, separate_observables=True)
                self.assertFalse(np.any(det), case.metadata)
                self.assertFalse(np.any(obs), case.metadata)
                mask = sinter.post_selection_mask_from_4th_coord(case.circuit)
                self.assertTrue(np.any(mask))  # online intentionally does not apply it

    def test_ip_against_exhaustive(self):
        dem = stim.DetectorErrorModel('''
error(0.1) D0 D1 D2 L0
error(0.2) D0
error(0.3) D1
error(0.15) D2 L0
''')
        d = IPDecoder(dem)
        patterns = np.array(list(itertools.product([0, 1], repeat=4)))
        for s in itertools.product([0, 1], repeat=3):
            s = np.array(s)
            eligible = patterns[np.all((d.H @ patterns.T).T % 2 == s, axis=1)]
            e = d.correction(s)
            self.assertAlmostEqual(float(d.weights @ e), float(np.min(eligible @ d.weights)))
        # Repeated targets across separator components cancel over GF(2).
        h, l, _ = matrices(stim.DetectorErrorModel('error(0.1) D0 L0 ^ D0 L0'))
        self.assertEqual(h.nnz, 0)
        self.assertEqual(l.nnz, 0)

    def test_ip_timeout_is_failure(self):
        from types import SimpleNamespace
        d = IPDecoder(stim.DetectorErrorModel('error(0.1) D0 L0'))
        with patch('reproduction.ip.milp', return_value=SimpleNamespace(status=1, message='time limit')):
            with self.assertRaises(RuntimeError):
                d.correction(np.array([1]))

    def test_ts_born_probabilities(self):
        ket = ts.qrm_initialization()
        self.assertAlmostEqual(ts.norm(ket), 1.0)
        bad = ts.gate_on_site(ts.GATE_Z, 0, ket)
        mixed = np.sqrt(.75)*ket + np.sqrt(.25)*bad
        discard, error = ts.X_measurement_postselected(mixed, mode='probability')
        self.assertAlmostEqual(discard, .25)
        self.assertAlmostEqual(error, 0)
        legacy, _ = ts.X_measurement_postselected(mixed, mode='legacy')
        self.assertAlmostEqual(legacy, 1-np.sqrt(.75))
        logical_bad = ts.transversal_gate(ts.GATE_Z, ket)
        mixed = np.sqrt(.75)*ket + np.sqrt(.25)*logical_bad
        discard, error = ts.X_measurement_postselected(mixed, mode='probability')
        self.assertAlmostEqual(discard, 0)
        self.assertAlmostEqual(error, .25)
        for gate in ['S', 'T']:
            d, e = ts.circuit_simulation(0, gate, mode='probability')
            self.assertAlmostEqual(d, 0)
            self.assertAlmostEqual(e, 0)

    def test_ts_accepted_weighting(self):
        with patch.object(ts, 'circuit_simulation', side_effect=[(.2, .1), (.8, .5)]):
            d, e, _ = ts.experiment(2, .001, 'S', mode='probability')
        self.assertAlmostEqual(d, .5)
        self.assertAlmostEqual(e, .18)

if __name__ == '__main__':
    unittest.main()
