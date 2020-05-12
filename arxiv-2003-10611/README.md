# tket_benchmarking
Scripts and circuits for benchmarking tket for arXiv:2003/10611 "t|ket⟩ : A Retargetable Compiler for NISQ Devices"

Circuits in "qasm_files" folder obtained from the Product Formula test set (all gate angles adapted to range from 1e-5 to 1e-2 to sit above qiskit's threshold), and IBM's Qiskit Developer Challenge test set; limited to 1e4 initial 2qb gates.

To benchmark pytket, requires: pytket==0.4.1

To benchmark Qiskit or Quilc, requires: pytket==0.5.2, pytket-qiskit==0.4.1, pytket-pyquil==0.4

`bench.py` runs the desired compiler/pass on the entire benchmark set and produces a CSV of results.

`usage: bench.py [-c <compiler>] [-b <backend>] [-p <pass>] [-s <set>]`
