from pytket import Circuit, OpType
from pytket.device import Device
from pytket.passes import FullPeepholeOptimise, SequencePass, PauliSimp, RebaseQuil, RebaseCirq, RebaseIBM, CXMappingPass, SynthesiseIBM
from pytket.predicates import CompilationUnit
from pytket.routing import Architecture, GraphPlacement
from pytket.qasm import circuit_from_qasm

import os, pandas, time, itertools, docker
from numpy import nan

import getopt
import sys

_BACKEND_FULL = "full"
_BACKEND_GOOGLE = "google"
_BACKEND_IBM = "ibm"
_BACKEND_RIGETTI = "rigetti"

backend_outfile_str = {
    _BACKEND_FULL : "FullConnectivity",
    _BACKEND_GOOGLE : "Sycamore",
    _BACKEND_IBM : "Rochester",
    _BACKEND_RIGETTI : "Aspen"
}

_COMPILER_TKET = "tket"
_COMPILER_QISKIT = "qiskit"
_COMPILER_QUILC = "quilc"

compiler_outfile_str = {
    _COMPILER_TKET : "Tket",
    _COMPILER_QISKIT : "Qiskit",
    _COMPILER_QUILC : "Quilc"
}

_PASS_FULLPASS = "FullPass"
_PASS_CHEMPASS = "ChemPass"
_PASS_QISO1 = "qisO1"
_PASS_QISO2 = "qisO2"
_PASS_QISO3 = "qisO3"

pass_outfile_str = {
    _PASS_FULLPASS : "Full",
    _PASS_CHEMPASS : "Chem",
    _PASS_QISO1 : "O1",
    _PASS_QISO2 : "O2",
    _PASS_QISO3 : "O3",
    "" : ""
}

_SET_ALL = "all"
_SET_UCCSD = "uccsd"

set_outfile_str = {
    _SET_ALL : "",
    _SET_UCCSD : "Chem"
}

def usage():
    print("usage: {source} [-c <compiler>] [-b <backend>] [-p <pass>] [-s <set>]".format(source=sys.argv[0]))
    print("<compiler> = {tket} (default), {qiskit}, {quilc}".format(tket=_COMPILER_TKET, qiskit=_COMPILER_QISKIT, quilc=_COMPILER_QUILC))
    print("<backend> = {full} (default), {google}, {ibm}, {rigetti}".format(full=_BACKEND_FULL, google=_BACKEND_GOOGLE, ibm=_BACKEND_IBM, rigetti=_BACKEND_RIGETTI))
    print("<pass> = {full} (default), {chem}, {qisO1}, {qisO2}, {qisO3}".format(full=_PASS_FULLPASS, chem=_PASS_CHEMPASS, qisO1=_PASS_QISO1, qisO2=_PASS_QISO2, qisO3=_PASS_QISO3))
    print("<set> = {all} (default), {uccsd}".format(all=_SET_ALL, uccsd=_SET_UCCSD))

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:b:p:s:")
except getopt.GetoptError as err:
    print(err)
    usage()
    exit()

compiler = _COMPILER_TKET
backend = _BACKEND_FULL
comp_pass = _PASS_FULLPASS
test_set = _SET_ALL

for o, v in opts:
    if o == '-c':
        if v in (_COMPILER_TKET, _COMPILER_QISKIT, _COMPILER_QUILC):
            compiler = v
        else:
            print("invalid compiler: {v}".format(v=v))
            usage()
            exit()
    elif o == '-b':
        if v in (_BACKEND_FULL, _BACKEND_IBM, _BACKEND_GOOGLE, _BACKEND_RIGETTI):
            backend = v
        else:
            print("invalid backend: {v}".format(v=v))
            usage()
            exit()
    elif o == '-p':
        if v in (_PASS_FULLPASS, _PASS_CHEMPASS, _PASS_QISO1, _PASS_QISO2, _PASS_QISO3):
            comp_pass = v
        else:
            print("invalid pass: {v}".format(v=v))
            usage()
            exit()
    elif o == '-s':
        if v in (_SET_ALL, _SET_UCCSD):
            test_set = v
        else:
            print("invalid test set: {v}".format(v=v))
            usage()
            exit()

if compiler == _COMPILER_QUILC:
    from pytket.pyquil import tk_to_pyquil, pyquil_to_tk

    import pyquil
    from pyquil.api import QVMCompiler
    from pyquil.api._config import PyquilConfig
    from pyquil import Program, get_qc
    from pyquil.device import isa_from_graph, Device as Device_
    import networkx as nx

    comp_pass = ""
    
elif compiler == _COMPILER_QISKIT:
    from pytket.qiskit import tk_to_qiskit, qiskit_to_tk

    from qiskit import QuantumCircuit
    from qiskit.compiler import transpile
    from qiskit.transpiler import CouplingMap

    if comp_pass == _PASS_FULLPASS: # Default
        comp_pass = _PASS_QISO3

outfile = "{set}Results_{comp}_{cpass}_{back}.csv".format(
    set=set_outfile_str[test_set],
    comp=compiler_outfile_str[compiler],
    cpass=pass_outfile_str[comp_pass],
    back=backend_outfile_str[backend])

### optimisation passes:
tketpass = FullPeepholeOptimise()
if compiler == _COMPILER_TKET and comp_pass == _PASS_CHEMPASS:
    tketpass = SequencePass([PauliSimp(), FullPeepholeOptimise()])

all_to_all_coupling = list()
for i in range(53):
    for j in range(i+1,53):
        all_to_all_coupling.append([i,j])

rigetti_coupling = [[0, 1], [1,2], [2,3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 0],
                    [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 8],
                    [2, 15], [3, 14]]

google_coupling = [[0, 5], [1, 5], [1, 6], [2, 6], [2, 7], [3, 8], [3, 9], [4, 9], [4,
                    10], [5, 11], [5, 12], [6, 12], [6, 13], [7, 13], [7, 14], [8, 14],
                    [8, 15], [9, 15], [9, 16], [10, 16], [11, 17], [12, 17], [12, 18],
                    [13, 18], [13, 19], [14, 19], [14, 20], [15, 20], [15, 21], [16, 21],
                    [16, 22], [17, 23], [17, 24], [18, 24], [18, 25], [19, 25], [19, 26],
                    [20, 26], [20, 27], [21, 27], [21, 28], [22, 28], [23, 29], [24, 29],
                    [24, 30], [25, 30], [25, 31], [26, 31], [26, 32], [27, 32], [27, 33],
                    [28, 33], [28, 34], [29, 35], [29, 36], [30, 36], [30, 37], [31, 37],
                    [31, 38], [32, 38], [32, 39], [33, 39], [33, 40], [34, 40], [35, 41],
                    [36, 41], [36, 42], [37, 42], [37, 43], [38, 43], [38, 44], [39, 44],
                    [39, 45], [40, 45], [40, 46], [41, 47], [41, 48], [42, 48], [42, 49],
                    [43, 49], [43, 50], [44, 50], [44, 51], [45, 51], [45, 52], [46, 52],
                    [47, 53], [48, 53], [48, 54], [49, 54], [49, 55], [50, 55], [50, 56],
                    [51, 56], [51, 57], [52, 57], [52, 58]]

ibm_coupling = [[0, 5],[0, 1],[1, 2],[1, 0],[2, 3],[2,
            1],[3, 4], [3, 2], [4, 6], [4, 3], [5, 9], [5, 0], [6,
            13], [6, 4], [7, 16], [7, 8], [8, 9], [8, 7], [9, 10], [9,
            8], [9, 5], [10, 11], [10, 9], [11, 17], [11, 12], [11,
            10], [12, 13], [12, 11], [13, 14], [13, 12], [13, 6], [14,
            15], [14, 13], [15, 18], [15, 14], [16, 19], [16, 7], [17,
            23], [17, 11], [18, 27], [18, 15], [19, 20], [19, 16],
            [20, 21], [20, 19], [21, 28], [21, 22], [21, 20], [22,
            23], [22, 21], [23, 24], [23, 22], [23, 17], [24, 25],
            [24, 23], [25, 29], [25, 26], [25, 24], [26, 27], [26,
            25], [27, 26], [27, 18], [28, 32], [28, 21], [29, 36],
            [29, 25], [30, 39], [30, 31], [31, 32], [31, 30], [32,
            33], [32, 31], [32, 28], [33, 34], [33, 32], [34, 40],
            [34, 35], [34, 33], [35, 36], [35, 34], [36, 37], [36,
            35], [36, 29], [37, 38], [37, 36], [38, 41], [38, 37],
            [39, 42], [39, 30], [40, 46], [40, 34], [41, 50], [41,
            38], [42, 43], [42, 39], [43, 44], [43, 42], [44, 51],
            [44, 45], [44, 43], [45, 46], [45, 44], [46, 47], [46,
            45], [46, 40], [47, 48], [47, 46], [48, 52], [48, 49],
            [48, 47], [49, 50], [49, 48], [50, 49], [50, 41], [51,
            44], [52, 48]]

### devices:
rigetti_device = Device(Architecture(rigetti_coupling))
google_sycamore_device = Device(Architecture(google_coupling))
ibm_rochester_device = Device(Architecture(ibm_coupling))
all_device = Device(Architecture(all_to_all_coupling))


def gen_tket_pass(optimisepass,backend:str):
    if backend == _BACKEND_FULL:
        return optimisepass
    elif backend == _BACKEND_RIGETTI:
        final_pass = RebaseQuil()
        device = rigetti_device
    elif backend == _BACKEND_GOOGLE:
        final_pass = RebaseCirq()
        device = google_sycamore_device
    elif backend == _BACKEND_IBM: 
        final_pass = RebaseIBM()
        device = ibm_rochester_device
    mapper = CXMappingPass(device, GraphPlacement(device))
    total_pass = SequencePass([optimisepass,mapper,SynthesiseIBM(),final_pass])
    return total_pass

def run_tket_pass(circ:Circuit,total_pass,backend:str):
    try:
        cu = CompilationUnit(circ)
        start_time = time.process_time()
        total_pass.apply(cu)
        time_elapsed = time.process_time() - start_time
        print(time_elapsed)
        circ2 = cu.circuit
        if backend in (_BACKEND_GOOGLE, _BACKEND_RIGETTI):
            two_qb_gate = OpType.CZ
        else:
            two_qb_gate = OpType.CX
        return [circ2.n_gates, circ2.depth(), circ2.n_gates_of_type(two_qb_gate), circ2.depth_by_type(two_qb_gate), time_elapsed]
    except Exception as e :
        print(e)
        print("t|ket> error")
        return [nan,nan,nan,nan,nan]

def run_qiskit_pass(fpath:str,backend:str):
    try:
        qsc = QuantumCircuit.from_qasm_file(fpath)
        if backend == _BACKEND_IBM:
            basis_gates = ['u1','u2','u3','cx']
            two_qb_gate = OpType.CX
            cm = CouplingMap(ibm_coupling)
        elif backend == _BACKEND_RIGETTI:
            basis_gates = ['u1','u2','u3','cx']
            two_qb_gate = OpType.CX
            cm = CouplingMap(rigetti_coupling)
        elif backend == _BACKEND_GOOGLE:
            basis_gates = ['u1','u2','u3','cx']
            two_qb_gate = OpType.CX
            cm = CouplingMap(google_coupling)
        else: # _BACKEND_FULL
            basis_gates = ['u1','u2','u3','cx']
            two_qb_gate = OpType.CX
            cm = None
        if comp_pass == _PASS_QISO1:
            opt_level = 1
        elif comp_pass == _PASS_QISO2:
            opt_level = 2
        elif comp_pass == _PASS_QISO3:
            opt_level = 3
        start_time = time.process_time()
        qsc2 = transpile(qsc,basis_gates=basis_gates,coupling_map=cm,optimization_level=opt_level)
        time_elapsed = time.process_time() - start_time
        print(time_elapsed)
        circ2 = qiskit_to_tk(qsc2)
        return [circ2.n_gates, circ2.depth(), circ2.n_gates_of_type(two_qb_gate), circ2.depth_by_type(two_qb_gate), time_elapsed]
    except Exception as e :
        print(e)
        print("qiskit error")
        return [nan,nan,nan,nan,nan]
    
def run_quilc_pass(circ:Circuit,backend:str):
    try:
        RebaseQuil().apply(circ)
        p_circ = tk_to_pyquil(circ)
        if backend == _BACKEND_IBM:
            devgraph = nx.from_edgelist(ibm_coupling)
            twoq_type = ['CZ']
            twoq_set = {OpType.CZ}
        elif backend == _BACKEND_RIGETTI:
            devgraph = nx.from_edgelist(rigetti_coupling)
            twoq_type = ['CZ', 'XY']
            twoq_set = {OpType.CZ, OpType.ISWAP}
        elif backend == _BACKEND_GOOGLE:
            devgraph = nx.from_edgelist(google_coupling)
            twoq_type = ['CZ']
            twoq_set = {OpType.CZ}
        elif backend == _BACKEND_FULL:
            devgraph = nx.complete_graph(circ.n_qubits)
            twoq_type = ['CZ', 'XY']
            twoq_set = {OpType.CZ, OpType.ISWAP}
        isa = isa_from_graph(devgraph, twoq_type=twoq_type)
        device = Device_("dev", {"isa" : isa.to_dict()})
        device._isa = isa
        qcompiler = QVMCompiler(PyquilConfig().quilc_url, device, timeout=600)
        start_time = time.time()
        compiled_pr = qcompiler.quil_to_native_quil(p_circ)
        time_elapsed = time.time() - start_time
        print(time_elapsed)
        circ2 = pyquil_to_tk(compiled_pr)
        return [circ2.n_gates, circ2.depth(), sum(circ2.n_gates_of_type(op) for op in twoq_set), circ2.depth_by_type(twoq_set), time_elapsed]
    except Exception as e :
        print(e)
        print("quilc error")
        return [nan,nan,nan,nan,nan]

stat_table = pandas.DataFrame({})

if test_set == _SET_ALL:
    test_table = pandas.read_csv("tket_paper_config.csv")
    filepath = "qasm_files"
elif test_set == _SET_UCCSD:
    test_table = pandas.read_csv("chem_config.csv")
    filepath = "chem_qasm"

total_pass = gen_tket_pass(tketpass,backend)

if compiler == _COMPILER_QUILC:
    dock = docker.from_env()
    qvm_container = dock.containers.run(image="rigetti/qvm", command="-S", detach=True, ports={5000:5000}, remove=True)
    quilc_container = dock.containers.run(image="rigetti/quilc:1.16.3", command="-R", detach=True, ports={5555:5555}, remove=True)
    time.sleep(4) # Give it time to boot up and start the servers

for index, row in test_table.iterrows():
    print(index)
    filename = row['Filename']
    fpath = os.path.join(filepath, filename)
    circ = circuit_from_qasm(fpath)
    if backend == _BACKEND_RIGETTI and circ.n_qubits > 16:
        results = [[filename] + [nan,nan,nan,nan,nan]]
    else:
        if circ.n_qubits > 53:
            raise Exception("Greater than 53 qubits: " + filename)
        if compiler == _COMPILER_TKET:
            results = [[filename] + run_tket_pass(circ,total_pass,backend)]
        elif compiler == _COMPILER_QISKIT:
            results = [[filename] + run_qiskit_pass(fpath,backend)]
        elif compiler == _COMPILER_QUILC:
            results = [[filename] + run_quilc_pass(circ,backend)]
    new_table_row = pandas.DataFrame(results, columns = ['Filename','Gate count', 'Depth', '2qb gate count', '2qb depth', 'Time elapsed'])
    print(new_table_row)
    stat_table = stat_table.append(new_table_row)
    stat_table.to_csv(outfile, index=False)

if compiler == _COMPILER_QUILC:
    qvm_container.stop()
    quilc_container.stop()
