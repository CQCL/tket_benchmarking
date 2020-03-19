# tket_benchmarking
Scripts and circuits for benchmarking tket

Circuits in "qasm_files" folder obtained from the Product Formula test set (all gate angles adapted to range from 1e-5 to 1e-2 to sit above qiskit's threshold), and IBM's Qiskit Developer Challenge test set; limited to 1e4 initial 2qb gates.

Used to benchmark pytket v0.4.1. To benchmark Qiskit and Quilc, pytket v0.5 is required for the newer (and faster) circuit analysis functions.

`bench.py` runs the desired compiler/pass on the entire benchmark set and produces a CSV of results.

`usage: bench.py [-c <compiler>] [-b <backend>] [-p <pass>] [-s <set>]`
