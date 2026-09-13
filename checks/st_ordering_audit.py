"""Exact S/T ordering for the 15-qubit model in Appendix D.4.

Enumerate the entire 15-bit error family, construct exact
probability polynomials, and certify positivity on 0 <= p <= 1/2 using rational
Bernstein coefficients. Optional independent state-vector checks use NumPy.
"""
import argparse
from collections import Counter
from fractions import Fraction as F
from itertools import combinations
import json
from math import comb
from pathlib import Path


def trim(a):
    a = list(a)
    while len(a) > 1 and not a[-1]:
        a.pop()
    return a


def add(a, b):
    return trim([(a[k] if k < len(a) else 0)+(b[k] if k < len(b) else 0)
                 for k in range(max(len(a), len(b)))])


def scale(a, c):
    return trim([x*c for x in a])


def mul(a, b):
    out = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return trim(out)


def power(a, n):
    out = [F(1)]
    for _ in range(n):
        out = mul(out, a)
    return out


def evaluate(a, p):
    result = F(0)
    for c in reversed(a):
        result = result*p+c
    return result


def bits(indices):
    return sum(1 << (i-1) for i in indices)


def span(generators):
    result = {0}
    for g in generators:
        result |= {x ^ g for x in result}
    return result


X_CHECKS = [bits([j for j in range(1, 16) if (j >> i) & 1]) for i in range(4)]
LOGICAL_X = bits(range(1, 8))
Z_CHECKS = [bits(x) for x in [
    [1,3,5,7], [3,2,7,6], [2,6,14,10], [6,14,12,4], [13,12,4,5],
    [12,8,9,13], [8,9,10,11], [9,1,11,3], [5,7,13,15], [10,11,15,14]]]


def model():
    cx = span(X_CHECKS)
    c = span(X_CHECKS+[LOGICAL_X])
    dual = {v for v in range(1 << 15) if all((v & u).bit_count() % 2 == 0 for u in c)}
    assert len(cx) == 16 and len(c) == 32 and len(dual) == 1024
    assert span(Z_CHECKS) == dual
    assert Counter(u.bit_count() for u in cx) == {0:1, 8:15}
    assert Counter(u.bit_count() for u in c) == {0:1, 7:15, 8:15, 15:1}
    return sorted(cx), sorted(c), dual


def deterministic_sums(error, group, dual, gate):
    total = 0
    for u in group:
        v = u & error
        w = v.bit_count()
        if gate == 'S':
            total += (-1)**w
        elif v in dual:
            assert w % 2 == 0
            total += (-1)**(w//2)
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--statevector-check', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    cx, c, dual = model()
    p, a, x = [F(0), F(1)], [F(1), F(-1)], [F(1), F(-2)]
    # Restricted dual-code weight enumerators verify each term of the
    # independent Heisenberg/projector derivation, for every group element.
    expected = {0:{0:1}, 7:{0:1,4:7}, 8:{0:1,4:14,8:1},
                15:{0:1,4:105,6:280,8:435,10:168,12:35}}
    for u in c:
        actual = Counter(v.bit_count() for v in dual if v & ~u == 0)
        assert actual == expected[u.bit_count()]
    def m(w):
        out = [F(0)]
        for k, n in expected[w].items():
            out = add(out, scale(mul(power(a,w-k),power(p,k)),n*(-1)**(k//2)))
        return out
    m7,m8,m15 = m(7),m(8),m(15)
    AS = scale(add([F(1)],scale(power(x,8),15)),F(1,16))
    AT = scale(add([F(1)],scale(m8,15)),F(1,16))
    BS = scale(add(add([F(1)],scale(power(x,8),15)),
                   add(scale(power(x,7),15),power(x,15))),F(1,32))
    BT = scale(add(add([F(1)],scale(m8,15)),add(scale(m7,15),m15)),F(1,32))
    polys = {'S':(AS,BS),'T':(AT,BT)}
    # Exhaustively average all 32768 deterministic physical X-error patterns.
    # After conjugation, S sends selected Heisenberg X factors to -X;
    # T sends them to +/-Y. Odd-Y expectations vanish for this real CSS state.
    sums = {g:[[0]*16,[0]*16] for g in ['S','T']}
    for error in range(1 << 15):
        weight = error.bit_count()
        for gate in ['S','T']:
            sa = deterministic_sums(error,cx,dual,gate)
            sb = deterministic_sums(error,c,dual,gate)
            assert 0 <= sb <= 2*sa <= 32
            sums[gate][0][weight] += sa
            sums[gate][1][weight] += sb
    for gate in ['S','T']:
        for k, divisor in [(0,16),(1,32)]:
            result = [F(0)]
            for w in range(16):
                result = add(result,scale(mul(power(p,w),power(a,15-w)),F(sums[gate][k][w],divisor)))
            assert result == polys[gate][k]
    JS,JT = add(AS,scale(BS,-1)),add(AT,scale(BT,-1))
    cross = add(mul(JS,AT),scale(mul(JT,AS),-1))
    assert cross[:3] == [0,0,0]
    Q = scale(cross[3:],8)
    assert len(Q) == 21 and Q[0] == 245
    # Q(t/2) = sum_j beta_j C(n,j) t^j (1-t)^(n-j).
    n = len(Q)-1
    beta = [sum(Q[k]*F(1,2)**k*F(comb(j,k),comb(n,k)) for k in range(j+1)) for j in range(n+1)]
    assert min(beta) == F(241,2048) and all(b > 0 for b in beta)
    expanded = [F(0)]
    for j,b in enumerate(beta):
        expanded=add(expanded,scale(mul(power(p,j),power(a,n-j)),b*comb(n,j)))
    assert expanded == [q*F(1,2)**k for k,q in enumerate(Q)]
    # A_T >= A_S: m8 >= (1-p)^8 >= (1-2p)^8 on [0,1/2].
    assert m8 == add(add(power(a,8),scale(mul(power(a,4),power(p,4)),14)),power(p,8))
    sv_checks = 0
    if args.statevector_check:
        import numpy as np
        from TS import qrm_state as ts
        ket = ts.qrm_initialization()
        assert abs(ts.norm(ket)-1) < 1e-12
        masks = [0,1,3,7,15,bits([1,4,8]),bits([1,3,5,7]),(1<<15)-1]
        for gate in ['S','T']:
            unitary = ts.GATE_S if gate == 'S' else ts.GATE_T
            inverse = ts.GATE_S_DAG if gate == 'S' else ts.GATE_T_DAG
            initial = ts.transversal_gate(unitary,ket)
            for mask in masks:
                state = initial.copy()
                for site in range(15):
                    if mask >> site & 1:
                        state = ts.gate_on_site(ts.GATE_X,site,state)
                state = ts.transversal_gate(inverse,state)
                # Direct tensor projector path from the actual implementation.
                discard,logical = ts.X_measurement_postselected(state,mode='probability')
                sa = F(deterministic_sums(mask,cx,dual,gate),16)
                sb = F(deterministic_sums(mask,c,dual,gate),32)
                assert abs((1-discard)-float(sa)) < 1e-12
                assert abs((1-discard)*(1-logical)-float(sb)) < 1e-12
                sv_checks += 1
    samples=[]
    for probability in [F(i,1000) for i in range(1,11)]:
        row={'p':str(probability)}
        for gate,(accept,good) in polys.items():
            A=evaluate(accept,probability);B=evaluate(good,probability)
            row[gate]={'discard':float(1-A),'logical_error':float((A-B)/A)}
        samples.append(row)
    # Counterexample: averaging need not preserve ordering after f(q)=2q-q^2.
    fs=lambda q:2*q-q*q
    assert F(1,10)>F(19,200)
    assert (fs(F(0))+fs(F(1,5)))/2 < fs(F(19,200))
    record={
        'verdict':'S/T ordering proved for the specified iid-X-noise 15-qubit model over 0 <= p <= 1/2.',
        'arithmetic':'Exact integers and fractions; float64 state-vector cross-check tolerance 1e-12',
        'groups':{'X_check_group':len(cx),'state_X_group':len(c),'Z_group':len(dual)},
        'exhaustive_error_patterns':32768,'direct_statevector_cases':sv_checks,
        'restricted_dual_weight_enumerators':expected,
        'polynomials_ascending':{g:{'accept':[str(v) for v in A],'accept_and_good':[str(v) for v in B]} for g,(A,B) in polys.items()},
        'logical_order_certificate':{'cross_product':'J_S*A_T-J_T*A_S = p^3*Q(p)/8',
            'Q_ascending':[str(v) for v in Q],'Bernstein_interval':['0','1/2'],
            'Bernstein_coefficients':[str(v) for v in beta],'minimum_coefficient':str(min(beta))},
        'leading_logical_coefficients':{'S':str(JS[3]),'T':str(JT[3])},
        'sample_exact_formula_evaluations':samples,
        'randomness':False,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+'\n')
    print('PASS: all 32768 error patterns; exact polynomial identities; positive Bernstein certificate on [0,1/2].')
    print(f'PASS: {sv_checks} independent direct state-vector cases.')
    print('At p=0.001:',json.dumps(samples[0]))

if __name__ == '__main__':
    main()
