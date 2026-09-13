# S/T comparison: corrected probability estimates

This note gives the corrected probability estimates for the 15-qubit noise
model in Appendix D.4 and Fig. 14 of *Non-Clifford quantum gate teleportation
with generalized lattice surgery*, Physical Review A 113, 062410 (2026).

The figure compares the part of the S/T calculations affected by X errors
around the transversal gate layer. Appendix D.4 uses it to compare both the
ordering of the S/T curves and the size of their difference relative to the
full-protocol rates.

The original state-vector estimator used norms instead of squared norms and
averaged conditional errors without acceptance weights. The corrected
calculation below preserves the S/T ordering over the full plotted interval
and preserves the order-of-magnitude comparison used in the article. The
original Fig. 14 table remains available in `published_data/fig14.csv`.

## Model and result

Consider precisely the model implemented in `simulations/st_comparison/statevector.py`: the ideal
15-qubit QRM logical-plus state; a physical transversal S or T layer; independent
physical X noise with probability p per qubit; the inverse transversal layer;
postselection on the four X stabilizers; and an X-logical measurement on qubits
1–7. These X errors are the model's only noise source. Let D_G be the discard probability
and L_G the error probability conditional on acceptance, using Born probabilities
and acceptance-weighted averaging over trajectories.

The claim proved here is

\[
D_S(p)\geq D_T(p),\qquad L_S(p)\geq L_T(p),\qquad 0\leq p\leq\tfrac12.
\]

Both inequalities are strict for p>0; equality holds at zero. The endpoint 1/2
is understood as the channel limit of the Gaussian-rotation implementation.
This result applies to the model specified above and covers the entire plotted
interval [0.001, 0.01].

## From trajectory estimates to ensemble probabilities

For one trajectory with nonzero acceptance, let a be the norm after the acceptance projector and b the
norm after both acceptance and the good-logical-outcome projector. The old code
uses d=1-a and e=1-b/a. Correct single-trajectory probabilities are

\[
D=1-a^2=2d-d^2,\qquad E=1-b^2/a^2=2e-e^2.
\]

The map f(q)=2q-q^2 is increasing on [0,1]. It preserves a pointwise order if
that order has already been established. The published program instead averages
over trajectories; corrected conditional rates also use different weights:

\[
D_G=\mathbb E[2d_G-d_G^2],\qquad
L_G=\frac{\mathbb E[(1-d_G)^2(2e_G-e_G^2)]}
{\mathbb E[(1-d_G)^2]}.
\]

Zero-acceptance trajectories carry zero weight in the conditional numerator and
denominator. An ordering of the old means alone is insufficient. For example, let q_S take
0 and 0.2 equally often, while q_T is constantly 0.095. Then the old means are
0.1>0.095, but the transformed means are 0.18<0.180975. This example shows why the QRM ensemble probabilities must be evaluated
explicitly to establish their ordering.

## Exact average channel and stabilizer reduction

The simulated Gaussian angle satisfies variance sigma^2=-2 log(1-2p). Its
symmetric distribution has average sine zero and average cosine 1-2p, so averaging
the random X rotation gives exactly the physical channel

\[
\mathcal E_p(\rho)=(1-p)\rho+pX\rho X.
\]

Acceptance probabilities and joint accepted-error probabilities are linear in
the density matrix. Therefore this channel gives their exact averages, and
dividing the two averages gives the correct conditional probability. The old norm estimator is nonlinear in the density matrix.

Let C_X be the binary span of the four X-check supports, and let C include the
logical X support as a fifth generator. Their weight distributions are

\[
W_{C_X}(z)=1+15z^8,\qquad W_C(z)=1+15z^7+15z^8+z^{15}.
\]

The initial pure state is the uniform superposition on C. The ten independent
Z-check generators in the actual initializer span C-perp. All these finite
statements are checked by complete exact enumeration in the accompanying script.
For u in C, the expectation of a Pauli string obtained by changing the X factors
on a subset v of u into Y is zero unless v is in C-perp; otherwise it is
(-1)^(|v|/2). Every vector in C-perp has even weight.

The effective single-site adjoint channel sends X to (1-2p)X for S, and to
(1-p)X plus or minus pY for T. The sign is irrelevant here because surviving
Y supports have even size. Restricted dual weight enumerators, checked for every
u in C, give the following exact T-channel moments. Set a=1-p and x=1-2p:

\[
M_7=a^7+7a^3p^4,
\]
\[
M_8=a^8+14a^4p^4+p^8,
\]
\[
M_{15}=a^{15}+105a^{11}p^4-280a^9p^6+435a^7p^8-168a^5p^{10}+35a^3p^{12}.
\]

The check projector averages over C_X; including the good-logical projector
averages over C. Write A for acceptance and B for acceptance AND good logical
outcome. Therefore

\[
A_S=\frac{1+15x^8}{16},\qquad B_S=\frac{1+15x^8+15x^7+x^{15}}{32},
\]
\[
A_T=\frac{1+15M_8}{16},\qquad B_T=\frac{1+15M_8+15M_7+M_{15}}{32},
\]
\[
D_G=1-A_G,\qquad L_G=\frac{A_G-B_G}{A_G}.
\]

These exact polynomial identities were additionally reconstructed by enumerating
all 32768 physical X-error patterns and summing the projector expectations by
error weight. Sixteen selected deterministic patterns were cross-checked through
the original full state-vector/tensor-projector implementation, with absolute
tolerance 10^-12. The latter checks are numerical; the polynomial certificate
itself uses only integers and exact fractions.

## Proof of ordering throughout the interval

For 0<=p<=1/2, a>=x>=0, so M_8>=a^8>=x^8. Consequently A_T>=A_S and D_S>=D_T.

For the logical rate, set J_G=A_G-B_G. Both denominators A_G are positive. Exact
expansion gives

\[
J_S A_T-J_T A_S=\frac{p^3}{8}Q(p),
\]

where Q is a degree-20 polynomial with Q(0)=245. Its complete rational
coefficients are saved in `validation/st-ordering/result.json`.
This is accompanied by an interval-wide positivity certificate:

\[
Q(t/2)=\sum_{j=0}^{20}\beta_j\binom{20}{j}t^j(1-t)^{20-j},
\qquad 0\leq t\leq1.
\]

All 21 Bernstein coefficients are strictly positive; their minimum is 241/2048.
The script verifies both the exact change-of-basis identity and positivity.
Because the Bernstein basis functions are nonnegative and sum to one, this
proves Q(p)>=241/2048 on [0,1/2]. Hence L_S>=L_T throughout that interval.
The finite enumeration supports an interval-wide proof because it constructs
exact probability polynomials for every possible physical error pattern; the
positivity argument then covers every real p in the interval.

The small-p expansions are

\[
L_S=35p^3+O(p^4),\qquad L_T=\frac{35}{8}p^3+O(p^4).
\]

## Consequence for the passage in the paper

Exact formula evaluations at p=0.001 give:

| Corrected quantity | S | T |
|---|---:|---:|
| Conditional logical error | 3.510537795740123e-8 | 4.381594004768761e-9 |
| Discard probability | 0.014895418951678322 | 0.007473802421354895 |

The logical-rate difference is about 3.07e-8, still of order 10^-8. The discard
difference is about 0.00742, compared with the approximately 0.004 quoted in the
paper. Both original relative-smallness comparisons remain valid for this
isolated model. The direction of the S/T ordering remains valid as well.

The corrected estimates therefore preserve both the ordering and the
order-of-magnitude comparison in Appendix D.4. The Fig. 14 values and the
approximate discard-rate difference quoted in the text change. The complete-protocol S/T substitution retains the interpretation given in
Appendix D.4: an estimate supported by this isolated-noise comparison.

## Reproduce the exact calculation

The script `checks/st_ordering_audit.py` verifies the stabilizer groups,
enumerates all 32768 physical error patterns, constructs the exact probability
polynomials and checks the positive Bernstein coefficients. It also compares
16 deterministic error patterns with the tensor-projector calculation in
`simulations/st_comparison/statevector.py`, using an absolute tolerance of 10^-12 for this numerical
cross-check. The polynomial and positivity calculations use exact integers
and fractions.

From the repository directory, with the supplied environment activated:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m checks.st_ordering_audit --statevector-check --output results/st-ordering.json
```

The calculation is deterministic. The JSON output contains the polynomial
coefficients, positivity certificate and evaluations at all ten plotted
physical error probabilities. A saved result is provided in
`validation/st-ordering/result.json`.

## Sample the S/T trajectories

The repository retains the original Fig. 14 table and provides two simulation
modes. `legacy` (the default) evaluates the original estimator; `probability`
uses squared norms and acceptance-weighted averaging. For a small-sample run
of the corrected estimator:

```bash
python -m reproduction.run ts --ts-mode probability --smoke --shots 100 --output results/ts-corrected
```

Increase `--shots` to improve the precision of the trajectory averages. The
exact calculation above evaluates the same corrected model deterministically.
