import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import scipy.sparse as sp
import stim
import sinter


def _dem_to_matrices(dem: stim.DetectorErrorModel) -> Tuple[sp.csr_matrix, sp.csr_matrix, np.ndarray]:
    """
    Convert a (possibly non-graph-like) DEM into:
        H: (num_detectors, num_errors) sparse parity-check matrix
        L: (num_observables, num_errors) sparse observable matrix
        p: (num_errors,) probabilities for each error mechanism

    IMPORTANT: We do NOT decompose errors. Each `error(p) ...` instruction -> one variable.
    """
    dem = dem.flattened()

    num_dets = dem.num_detectors
    num_obs = dem.num_observables

    det_rows: List[int] = []
    det_cols: List[int] = []

    obs_rows: List[int] = []
    obs_cols: List[int] = []

    probs: List[float] = []

    col = 0
    for inst in dem:
        if inst.type != "error":
            continue
        args = inst.args_copy()
        if len(args) != 1:
            raise ValueError(f"Unexpected error instruction args: {args}")

        p = float(args[0])
        # Clamp away from 0/1 to avoid infinities in weights / log odds.
        p = min(max(p, 1e-12), 1 - 1e-12)

        targets = inst.targets_copy()
        # Note: ignore separators. We treat the whole instruction as one correlated mechanism.
        for t in targets:
            if t.is_separator():
                continue
            if t.is_relative_detector_id():
                det_rows.append(t.val)
                det_cols.append(col)
            elif t.is_logical_observable_id():
                obs_rows.append(t.val)
                obs_cols.append(col)
            else:
                # e.g. gauge targets etc. Usually not present in standard DEM.
                pass

        probs.append(p)
        col += 1

    num_errs = col
    H = sp.coo_matrix(
        (np.ones(len(det_rows), dtype=np.uint8), (np.array(det_rows), np.array(det_cols))),
        shape=(num_dets, num_errs),
    ).tocsr()

    L = sp.coo_matrix(
        (np.ones(len(obs_rows), dtype=np.uint8), (np.array(obs_rows), np.array(obs_cols))),
        shape=(num_obs, num_errs),
    ).tocsr()

    return H, L, np.array(probs, dtype=np.float64)


# ---------------------------
# BP-OSD decoder (recommended)
# ---------------------------

@dataclass
class BPOSDHypergraphDecoder(sinter.Decoder):
    """
    A sinter Decoder that runs BP-OSD on the linear system derived from DEM.
    """
    bp_method: str = "ms"         # depends on ldpc version; common: "ms" (min-sum) or "bp"
    max_iter: int = 50
    osd_order: int = 10

    def compile_decoder_for_dem(self, dem: stim.DetectorErrorModel) -> sinter.CompiledDecoder:
        return _CompiledBPOSDHypergraphDecoder(
            dem=dem,
            bp_method=self.bp_method,
            max_iter=self.max_iter,
            osd_order=self.osd_order,
        )


class _CompiledBPOSDHypergraphDecoder(sinter.CompiledDecoder):
    def __init__(self, dem: stim.DetectorErrorModel, bp_method: str, max_iter: int, osd_order: int):
        self.H, self.L, self.p = _dem_to_matrices(dem)
        self.num_obs = dem.num_observables

        # ldpc API differs slightly across versions; this is the common one.
        # If import fails or signature differs, see note at the end.
        from ldpc import BpOsdDecoder  # type: ignore

        # channel_probs: Pr(bit=1) for each variable
        self._decoder = BpOsdDecoder(
            self.H,
            channel_probs=self.p,
            bp_method=bp_method,
            max_iter=max_iter,
            osd_order=osd_order,
        )

    def decode_shots(self, dets: np.ndarray) -> np.ndarray:
        """
        dets: shape (shots, num_detectors), dtype bool/uint8
        returns: predicted observables, shape (shots, num_observables), dtype bool
        """
        dets = np.asarray(dets)
        if dets.dtype != np.uint8 and dets.dtype != np.bool_:
            dets = dets.astype(np.uint8)

        shots = dets.shape[0]
        out = np.zeros((shots, self.num_obs), dtype=np.uint8)

        # BP-OSD通常逐条syndrome解码（有些版本支持batch，这里先用最通用写法）
        for k in range(shots):
            s = dets[k].astype(np.uint8)
            e_hat = self._decoder.decode(s)  # expected shape (num_errors,), 0/1
            e_hat = np.asarray(e_hat, dtype=np.uint8)

            # observable flips = (L @ e_hat) mod 2
            o = (self.L @ e_hat) & 1
            out[k, :] = np.asarray(o, dtype=np.uint8).reshape(-1)

        return out.astype(np.bool_)


# ---------------------------
# ILP decoder (exact ML; slow)
# ---------------------------

@dataclass
class ILPHypergraphDecoder(sinter.Decoder):
    """
    Exact ML via integer programming.
    WARNING: Only practical for small instances / few shots.
    """
    solver_name: str = "CBC"  # python-mip default; can also use "GUROBI" if available

    def compile_decoder_for_dem(self, dem: stim.DetectorErrorModel) -> sinter.CompiledDecoder:
        return _CompiledILPHypergraphDecoder(dem=dem, solver_name=self.solver_name)


class _CompiledILPHypergraphDecoder(sinter.CompiledDecoder):
    def __init__(self, dem: stim.DetectorErrorModel, solver_name: str):
        self.H, self.L, self.p = _dem_to_matrices(dem)
        self.num_obs = dem.num_observables
        self.solver_name = solver_name

        # log-likelihood ratio weights for ML:
        # minimize sum w_i * e_i, where w_i = log((1-p)/p)
        self.w = np.log((1 - self.p) / self.p)

        # Pre-extract sparse structure for constraints
        self.H_csr = self.H.tocsr()

    def _solve_one(self, s: np.ndarray) -> np.ndarray:
        from mip import Model, xsum, BINARY, INTEGER, OptimizationStatus  # type: ignore

        m = Model(sense="MIN", solver_name=self.solver_name)
        m.verbose = 0

        n_err = self.H.shape[1]
        n_det = self.H.shape[0]

        e = [m.add_var(var_type=BINARY) for _ in range(n_err)]
        t = [m.add_var(var_type=INTEGER, lb=0) for _ in range(n_det)]  # parity slack

        # constraints: sum_j H[r,j]*e[j] - 2*t[r] == s[r]
        for r in range(n_det):
            start, end = self.H_csr.indptr[r], self.H_csr.indptr[r + 1]
            cols = self.H_csr.indices[start:end]
            m += xsum(e[c] for c in cols) - 2 * t[r] == int(s[r])

        m.objective = xsum(float(self.w[i]) * e[i] for i in range(n_err))
        status = m.optimize(max_seconds=30)

        if status not in {OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE}:
            # Fallback: if ILP fails, return "no correction"
            return np.zeros(n_err, dtype=np.uint8)

        e_hat = np.array([int(v.x + 0.5) for v in e], dtype=np.uint8)
        return e_hat

    def decode_shots(self, dets: np.ndarray) -> np.ndarray:
        dets = np.asarray(dets)
        if dets.dtype != np.uint8 and dets.dtype != np.bool_:
            dets = dets.astype(np.uint8)

        shots = dets.shape[0]
        out = np.zeros((shots, self.num_obs), dtype=np.uint8)

        for k in range(shots):
            s = dets[k].astype(np.uint8)
            e_hat = self._solve_one(s)
            o = (self.L @ e_hat) & 1
            out[k, :] = np.asarray(o, dtype=np.uint8).reshape(-1)

        return out.astype(np.bool_)
