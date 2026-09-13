"""Minimum-weight error-configuration decoding with SciPy/HiGHS.

The solver uses the undecomposed detector error model. Equally weighted
corrections can be resolved differently from the published TensorQEC solver.
"""
import numpy as np
from scipy import sparse
from scipy.optimize import Bounds, LinearConstraint, milp


def matrices(dem):
    rows, cols, lrows, lcols, probabilities = [], [], [], [], []
    for instruction in dem.flattened():
        if instruction.type != 'error':
            continue
        j = len(probabilities)
        probabilities.append(instruction.args_copy()[0])
        for t in instruction.targets_copy():
            if t.is_relative_detector_id():
                rows.append(t.val); cols.append(j)
            elif t.is_logical_observable_id():
                lrows.append(t.val); lcols.append(j)
    n = len(probabilities)
    def build(r, c, height):
        a = sparse.coo_matrix((np.ones(len(r), dtype=np.int32), (r, c)), shape=(height, n)).tocsr()
        a.data %= 2
        a.eliminate_zeros()
        return a
    return build(rows, cols, dem.num_detectors), build(lrows, lcols, dem.num_observables), np.array(probabilities)


class IPDecoder:
    def __init__(self, dem, timeout=30):
        self.H, self.L, p = matrices(dem)
        self.timeout = timeout
        n, m = self.H.shape[1], self.H.shape[0]
        if np.any((p <= 0) | (p >= 1)):
            raise ValueError('IP requires DEM probabilities strictly between zero and one')
        self.weights = np.log1p(-p) - np.log(p)
        self.objective = np.r_[self.weights, np.zeros(m)]
        self.constraints = sparse.hstack([self.H, -2 * sparse.eye(m)], format='csc')
        self.bounds = Bounds(np.zeros(n + m), np.r_[np.ones(n), np.asarray(self.H.sum(axis=1)).ravel() // 2])

    def correction(self, syndrome):
        n = self.H.shape[1]
        if n == 0:
            if np.any(syndrome):
                raise ValueError('Nonzero syndrome with empty DEM')
            return np.zeros(0, dtype=np.uint8)
        result = milp(self.objective, integrality=np.ones(len(self.objective)),
                      bounds=self.bounds,
                      constraints=LinearConstraint(self.constraints, syndrome, syndrome),
                      options={'time_limit': self.timeout, 'mip_rel_gap': 0.0})
        if result.status != 0:
            raise RuntimeError(f'IP failed to prove optimality: {result.message}')
        e = np.rint(result.x[:n]).astype(np.uint8)
        if not np.array_equal((self.H @ e) % 2, syndrome):
            raise RuntimeError('IP correction violates the measured syndrome')
        return e

    def decode_batch(self, detectors):
        return np.array([(self.L @ self.correction(s)) % 2 for s in detectors], dtype=np.uint8)
