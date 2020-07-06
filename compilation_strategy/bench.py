# Script to read `QubitPauliOperator` objects from file and test
# compilation methods.

# The Bravyi-Kitaev and Jordan-Wigner operators have symbolic
# expressions for coefficients, as they are generated using EUMEN,
# which allows for symbolic terms for variational algorithms. The
# Parity operators are from Qiskit Aqua, and are therefore not
# symbolic. This does not affect the compilation metrics, as the
# angles are not Clifford regardless.


import os
import pickle
import json
import pandas as pd
import datetime

from pytket.circuit import Qubit, Circuit, OpType, fresh_symbol, PauliExpBox
from pytket.utils import gen_term_sequence_circuit
from pytket.utils import QubitPauliOperator
from pytket.transform import Transform, PauliSynthStrat, CXConfigType
from pytket.pauli import Pauli

with open("orbital_lut.txt") as json_file:
    orbitals_lookup_table = json.load(json_file)

cols = [
    "Circuit Name",
    "Active Spin Orbitals",
    "Naive CX Count",
    "Naive CX Depth",
    "Pairwise CX Count",
    "Pairwise CX Depth",
    "Set CX Count",
    "Set CX Depth",
    "Set Compile Time",
]

for encoding_name in ("BK", "JW", "P"):
    op_directory = "operators/{}_operators".format(encoding_name)
    results_file = "results/{}_results.csv".format(encoding_name)
    stat_table = pd.DataFrame({})
    for filename in os.listdir(op_directory):
        path = op_directory + "/" + filename
        with open(path, "rb") as pickle_in:
            qubit_pauli_operator = pickle.load(pickle_in)
        name = filename.replace(".pickle", "")
        print(name)
        active_spin_orbitals = orbitals_lookup_table[name]

        # Qiskit removed 2 qubits per circuit for us using Z2
        # Symmetries for the Parity encoding
        if encoding_name == "P":
            n_qubits = active_spin_orbitals - 2
        else:
            n_qubits = active_spin_orbitals

        initial_circ = Circuit(n_qubits)

        print("sequencing")
        t1_a = datetime.datetime.now()
        set_synth_circuit = gen_term_sequence_circuit(
            qubit_pauli_operator, initial_circ
        )
        t1_b = datetime.datetime.now()
        print(
            "Partitions: {}".format(set_synth_circuit.n_gates_of_type(OpType.CircBox))
        )

        naive_circuit = set_synth_circuit.copy()
        pairwise_circuit = set_synth_circuit.copy()

        Transform.DecomposeBoxes().apply(naive_circuit)
        # Naive construction: decompose each Pauli exponential invidually
        naive_cx_count = naive_circuit.n_gates_of_type(OpType.CX)
        naive_cx_depth = naive_circuit.depth_by_type(OpType.CX)

        print("pairwise synth")
        # Pairwise construction: decompose each Pauli exponential
        # two-by-two, using balanced trees of CX gates.
        Transform.UCCSynthesis(
            PauliSynthStrat.Pairwise, CXConfigType.Tree
        ).apply(pairwise_circuit)
        pairwise_cx_count = pairwise_circuit.n_gates_of_type(OpType.CX)
        pairwise_cx_depth = pairwise_circuit.depth_by_type(OpType.CX)

        print("set synth")
        t1_c = datetime.datetime.now()
        # Full set-based synthesis: diagonalise each commuting set, then
        # synthesise with phase polynomials.
        Transform.UCCSynthesis(PauliSynthStrat.Sets, CXConfigType.Tree).apply(
            set_synth_circuit
        )
        t1_d = datetime.datetime.now()
        set_synth_cx_count = set_synth_circuit.n_gates_of_type(OpType.CX)
        set_synth_cx_depth = set_synth_circuit.depth_by_type(OpType.CX)

        set_compile_time = (t1_b - t1_a + t1_d - t1_c).total_seconds()
        print("Time for set-based: {}".format(set_compile_time))

        results = [
            [
                name,
                active_spin_orbitals,
                naive_cx_count,
                naive_cx_depth,
                pairwise_cx_count,
                pairwise_cx_depth,
                set_synth_cx_count,
                set_synth_cx_depth,
                set_compile_time,
            ]
        ]
        new_table_row = pd.DataFrame(results, columns=cols)
        print(new_table_row)
        stat_table = stat_table.append(new_table_row)
        stat_table = stat_table.sort_values(by=['Active Spin Orbitals', 'Circuit Name'])
        stat_table.to_csv(results_file, index=False)
