import itertools

# All length 4 lists of Paulis. Each list corresponds to a 4-qubit
# Pauli string.
strings = list(itertools.product(["I", "X", "Y", "Z"], repeat=4))

# Each commuting set of Pauli gadgets is generated by at most 4
# strings, so it is sufficient to test over all combinations of 4
# strings.
string_sets = list(itertools.combinations(strings, 4))

print(len(strings))
print(len(string_sets))

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


# Test whether a commuting set has a compatible pair.
def any_solvable(s):
    qubits = list(zip(*s))
    for q1, q2 in itertools.combinations(qubits, 2):
        if solved(q1) or solved(q2) or solvable(q1, q2):
            return True
    return False


# Check if two Pauli strings commute.
def commutes(p1, p2):
    diff_count = 0
    for a, b in zip(p1, p2):
        if a != b and a != "I" and b != "I":
            diff_count += 1
    return diff_count % 2 == 0


# Check that all Pauli strings in a set commute.
def commuting_set(s):
    for p1, p2 in itertools.combinations(s, 2):
        if not commutes(p1, p2):
            return False
    return True


for i, ss in enumerate(string_sets):
    # Progress check
    if i % 1000000 == 0:
        print(i)
    if not commuting_set(ss):
        continue
    if not any_solvable(ss):
        print("Incompatible combination found: {}".format(ss))
        exit()

print("All combinations compatible.")
