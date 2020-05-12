# tket_benchmarking
Scripts and circuits for benchmarking quantum compilation platforms. This is designed to be maintained to keep a regular comparison between the latest versions of quantum compilation software, including tket, Qiskit, and Quilc. Current supported versions are:

pytket==0.5.4
qiskit==0.18.0 (requires pytket-qiskit==0.4.1)
pyquil==2.19.0 (requires pytket-pyquil==0.4)

Circuits in "qasm_files" folder obtained from the Product Formula test set (all gate angles adapted to range from 1e-5 to 1e-2 to sit above qiskit's threshold), and IBM's Qiskit Developer Challenge test set; limited to 1e4 initial 2qb gates.

`bench.py` runs the desired compiler/pass on the entire benchmark set and produces a CSV of results.

`usage: bench.py [-c <compiler>] [-b <backend>] [-p <pass>] [-s <set>]`
