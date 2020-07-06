import itertools

# All length 3 lists of Paulis. Each list corresponds to a single
# qubit to be diagonalised over 3 gadgets.
qubits = list(itertools.product(["I", "X", "Y", "Z"], repeat=3))

# All pairs of length 3 lists of Paulis. Each pair corresponds to a
# pair of qubits.
qubit_pairs = list(itertools.product(qubits, repeat=2))

# If a list of Paulis has only a single non-I Pauli type, the
# corresponding qubit is trivially diagonalisable using single-qubit
# Cliffords.
def solved(q):
    s = set(q)
    s.discard("I")
    return len(s) <= 1


# If 2 lists of Paulis are a compatible pair (cf Theorem 5.2) they can
# be diagonalised using Clifford gates.
def solvable(q, r):
    for a in ["X", "Y", "Z"]:
        for b in ["X", "Y", "Z"]:
            ok = True
            for qi, ri in zip(q, r):
                if qi in ["I", a] and ri not in ["I", b]:
                    ok = False
                    break
                elif qi not in ["I", a] and ri in ["I", b]:
                    ok = False
                    break
            if ok:
                return True
    return False


for q1, q2 in qubit_pairs:
    if not solved(q1) and not solved(q2) and not solvable(q1, q2):
        print("Incompatible combination found: {}, {}".format(q1, q2))
        exit()

print("All combinations compatible.")
