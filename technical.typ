#import "@preview/hetvid:0.1.0": *
#import "@local/braket:0.1.0": *
#import "@preview/tablem:0.2.0": tablem, three-line-table

#show: hetvid.with(
    title: "Technical details in simulating magic preparation",
    author: "Wang Yifei",
    affiliation: [Institute for Advanced Study, Tsinghua University],
    date-created: "2025-07-28",
    date-modified: "2025-07-28",
    // math-font: ("STIX Two Math"),
    abstract: [In this document, we discuss the technical details in simulating magic preparation circuit using generalized lattice surgery.],
)

= Simulating QRM code preparation 

== Handling or measurement errors

By a measurement error, we mean that we project the state correctly, but read the wrong result.
A computational basis measurement with error rate $p$ is formulated by measurement channel
$ cal(M)_p rho &= sum_(m=0,1)((1-p)(Pi_m rho Pi_m, m) + p(Pi_m rho Pi_m, m+1)) \
 &= sum_(m=0,1) ((1-p)Pi_m rho Pi_m + p Pi_(m+1)rho Pi_(m+1), m). $
Here 
$ Pi_(m) = (1+(-1)^m Z)/2, quad Pi_(m+1) = X Pi_m X. $
Therefore a measurement error is simulated by two correlated $X$ errors before and after the measurement.

*Conclusion:*
In real simulation, if the measurement is followed by a reset, we just put an $X$ error before the measurement.
If we will do more things after the measurement, we must put correlated errors.

== Rounds of final measurement

We would like to think about how many rounds of measurements is needed in the final destructive measurement.
Consider a general setting: we want to measure a logical $X$ destructively on a code with $Z$-distance $d$.
Before measurement, there are idling depolarization error.
And there are measurement errors.
Let each error occur independently with probability $p$.
Suppose we post-selection on the syndrome of $X$-checks.

As we have discussed, we can decompose the measurement error into correlated $Z$ errors before and after the measurement (note that we are measuring $Z$).
Also, only the $Z$ channel of depolarizion affect the measurement result.
We can therefore merge these errors before the measurement, leading to $Z$ errors with probability of order $p$.
So the probability of a logical $Z$ error after post-selection is trivially $O(p^d)$.
In this case measuring more than one round can only enlarge the coefficient of the logical error rate.
So one round of measurement is enough.

Note that the decomposition of measurement errors simplify our analysis:
we do not need to analyse the complex situation of mixing two kinds of errors.
One round of measurement even free us from considering the correlation of decomposed errors.

*Conclusion:*
One round of destructive logical measurement is optimal.

== Optimization of syndrome measurement without flags

In simulating the $bracket.double.l 15,1,3 bracket.double.r$ QRM code, we need to first prepare a logical $ket(overline(+))$ state.
This is done by preparing a product state $ket(+)^(times.circle 15)$ and measuring a complete set of $Z$-checks.
The code has redundancy in the $Z$-checks.
Trivially we choose the 4-qubit checks. 
However, we still have some freedom in choosing the checks.
Our goal is two-fold:
+ The measurement can be parallelised into 4 rounds of CNOTs.
+ Each qubit is checked in a balanced number of times.
The first requirement is natural, although designing it is like a Sudoku game.
The second requirement, on the one hand, makes the first easier to satisfy (you cannot achieve requirement 1 if there is a qubit being checked more than 4 times),
and on the other hand, ensures good error suppression, as we will analyse later.

I number the qubits in QRM code as the normal Reed-Muller way.
Qubits are labelled by 4-bit binaries with 0000 excluded.
// #align(center)[#table({

// })]

#three-line-table[
|0001|0010|0011|0100|0101|0110|0111|1000|1001|1010|1011|1100|1101|1110|1111|
|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|
]
Put on tetrahedron:
- vertices: qubits with one '1' (1, 2, 4, 8)
- edges: qubits with 2 '1's, or adding 2 vertices (3, 5, 6, 9, 10, 12)
- faces: qubits with 3 '1's, or adding 3 vertices (7, 11, 13, 14)
- body: qubits with 4 '1's, or adding 4 vertices (15)
We choose the $Z$-checks by the following rules:
- For each of the 4 triangles 124, 248, 481, 812, check two quadrilaterals adjcent to the edge with first two labels. 
  This gives 8 checks, 
  each vertex is checked twice, 
  middle points of edges 12, 24, 48, 81 each is checked 3 times, 
  middle points of edges 14, 28 each is checked twice, 
  each face center is checked twice. 
  One can check that $4 times 2 + 4 times 3 + 2 times 2 + 4 times 2 = 32 = 8 * 4$.
- add two checks that links edges 14, 28 and the body center. 
  Now middle points of these two edges each is checked 1 more time,
  each face center is checked 1 more time,
  and the body center is checked twice.
Finally, each vertex and the body center is checked 2 times (totally 10),
each edge center and face center is checked 3 times (totally 30).
The list of checks are as follows.
```py
QRM_Z_CHECKS_REDUCED = [
[1,3,5,7],
[3,2,7,6],
[2,6,14,10],
[6,14,12,4],
[13,12,4,5],
[12,8,9,13],
[8,9,10,11],
[9,1,11,3],
[5,7,13,15],
[10,11,15,14]
]
```
We have designed this list carefully such that a number only occurs once in each column.
This meets our 2 requirements.

Now the 10 checks can have different measurement results.
These results can influence the gate to be applied.
We infer from the measurement results that on which qubits we should apply $X$ operators to bring it to the standard QRM code.
Suppose we should apply an $X$ string $S_X$.
Now the logical state of the code abtained and the standard QRM code has the relation
$ ket(overline(+)) = S_X ket(overline(+))_("std"), quad ket(overline(-)) = (-1)^(w(S_X)) S_X ket(overline(-))_("std"). $
Consequently, in computational basis,
$ ket(overline(0)) = S_X overline(X)^(w(S_X)) ket(overline(0))_("std"), quad ket(overline(1)) = S_X overline(X)^(w(S_X)) ket(overline(1))_("std"). $
Therefore, the logical $T$ on the new code 

Let's analyse the error propagation in measuring the listed checks.
There are three types of errors: errors in data qubits, errors in ancilla qubits and measurement errors.
If there is only errors in data qubits, code distance and post-selection ensures a $p^3$ logical error suppression.
If there is only measurement errors, it can always be detected.
For errors in ancilla, $X$ errors can always be detected and $Z$ error can be spread to data qubits, which when affecting one data qubits, can be viewed as a single data qubit error,
but when affecting two data qubits, introduces correlated two-qubit $Z$ errors in data qubits.
The latter case can destroy the $p^3$ suppression in the final destructive measurement.
_This is the first dangeous point._
Let's consider combined errors.


== Optimization of syndrome measurement with flags