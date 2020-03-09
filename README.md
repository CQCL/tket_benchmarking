# tket_benchmarking
Scripts and circuits for benchmarking tket

Circuits obtained from the Cowtan et al UCCSD test set, the Product Formula test set (all gate angles adapted to range from 1e-5 to 1e-2 to sit above qiskit's threshold), and IBM's Qiskit Developer Challenge test set; limited to 1e4 initial 2qb gates.

`bench.py` runs the desired compiler/pass on the entire benchmark set and produces a CSV of results.

`usage: bench.py [-c <compiler>] [-b <backend>] [-p <pass>]`
