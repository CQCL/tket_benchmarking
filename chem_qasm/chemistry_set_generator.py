# Script for generating the example circuits in the Unitary Coupled Cluster 
# optimisation benchmark set
#
# Requires qiskit-aqua~=0.6.4

from qiskit.chemistry.drivers.pyscfd import PySCFDriver
from qiskit.chemistry import FermionicOperator
from qiskit.chemistry.core import Hamiltonian, QubitMappingType
from qiskit.chemistry.components.initial_states import HartreeFock
from qiskit.chemistry.components.variational_forms import UCCSD
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.transpiler.passes.basis.unroller import Unroller
import numpy as np

molecules = {
    'H2' : 'H .0 .0 .0; H .0 .0 0.75',
    # 'H4' : 'H .0 .0 .0; H .0 .0 0.75; H .0 0.75 .0; H .0 0.75 0.75',
    # 'H8' : 'H .0 .0 1.0; H .0 0.707 0.707; H .0 1.0 .0; H .0 0.707 -0.707; H .0 .0 -1.0; H .0 -0.707 -0.707; H .0 -1.0 .0; H .0 -0.707 0.707',
    # 'LiH' : 'Li .0 .0 .0; H .0 .0 0.75',
    # 'NH' : 'N .0 .0 .0; H .0 .0 0.75',
    # 'H2O' : 'H 0. 1.004 -0.35615; O 0. 0. 0.05982; H 0. -1.004 -0.35615',
    # 'CH2' : 'H 0. 1.004 -0.35615; C 0. 0. 0.05982; H 0. -1.004 -0.35615',
    # 'C2H4' : 'C .000000 .000000 .667480; C .000000 .000000 -.667480; H .000000 .922832 1.237695; H .000000 -.922832 1.237695; H .000000 .922832 -1.237695; H .000000 -.922832 -1.237695'
}

bases = [
    # 'sto3g',
    # '631g',
    # 'ccpvdz',
    'ccpvtz'
]

qubit_mappings = {
    'JW' : QubitMappingType.JORDAN_WIGNER,
    'P' : QubitMappingType.PARITY,
    'BK' : QubitMappingType.BRAVYI_KITAEV
}

for basis in bases :
    for mol_name, molecule_str in molecules.items() :
        driver = PySCFDriver(molecule_str, basis=basis)
        mol = driver.run()
        for qm_name, qubit_mapping in qubit_mappings.items() :
            for freeze_core in [True, False] :
                core = Hamiltonian(qubit_mapping=qubit_mapping, two_qubit_reduction=False, freeze_core=freeze_core)
                qubitOp, _ = core.run(mol)
                n_qubits = qubitOp.num_qubits
                n_orbitals = core._molecule_info['num_orbitals']
                n_electrons = core._molecule_info['num_particles']
                # n_qubits = mol.one_body_integrals.shape[0]
                # n_qubits = mol.num_orbitals
                # n_electrons = mol.num_alpha + mol.num_beta - mol.molecular_charge
                # n_orbitals = mol.num_orbitals
                # ferOp = FermionicOperator(h1=mol.one_body_integrals, h2=mol.two_body_integrals)
                # if freeze_core and mol.core_orbitals:
                #     core = mol.core_orbitals
                #     freeze_alphas = [i for i in core if i < mol.num_alpha]
                #     freeze_betas = [i + n_orbitals for i in core if i < mol.num_beta]
                #     freeze_list = np.append(np.array(freeze_alphas), np.array(freeze_betas))
                #     print(freeze_list)
                #     ferOp, _ = ferOp.fermion_mode_freezing(freeze_list)
                #     n_qubits -= len(freeze_list)
                #     n_electrons -= len(freeze_list)
                # qubitOp = ferOp.mapping(map_type=qubit_mapping, threshold=1e-8)
                qubitOp.chop(1e-10)
                # print(n_qubits)
                # print(n_orbitals)
                initial_hf = HartreeFock(num_qubits=n_qubits, num_orbitals=n_orbitals, qubit_mapping=core._qubit_mapping, two_qubit_reduction=False, num_particles=n_electrons)
                var_form = UCCSD(num_qubits=n_qubits, num_orbitals=n_orbitals, num_particles=n_electrons, depth=1, initial_state=initial_hf, qubit_mapping=core._qubit_mapping, two_qubit_reduction=False)
                number_amplitudes = len(var_form._single_excitations) + len(var_form._double_excitations)
                amplitudes = [1e-4]*number_amplitudes
                circuit = var_form.construct_circuit(amplitudes)
                dag = circuit_to_dag(circuit)
                dag = Unroller(['cx', 'u1', 'u3']).run(dag)
                circuit = dag_to_circuit(dag)
                qasm = circuit.qasm()
                filename = '{m}_{f}_{q}_{b}.qasm'.format(m=mol_name, f=('frz' if freeze_core else 'cmplt'), q=qm_name, b=basis)
                with open(filename, 'w') as ofile :
                    ofile.write(qasm)
                print(filename)
                print(circuit.count_ops())
