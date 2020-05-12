from pytket import Circuit, circuit_from_qasm, OpType
import os, pandas

stat_table = pandas.DataFrame({})
for filename in os.listdir("qasm_files"):
    fpath = os.path.join("qasm_files", filename)
    circ = circuit_from_qasm(fpath)
    new_stats = [[filename, circ.n_gates, circ.depth(), circ.n_gates_of_type(OpType.CX), circ.depth_by_type(OpType.CX)]]
    new_table_row = pandas.DataFrame(new_stats, columns = ['Filename','Gate count', 'Depth', '2qb gate count', '2qb depth'])
    stat_table = stat_table.append(new_table_row)
stat_table = stat_table.sort_values(by=['2qb gate count','2qb depth'])
stat_table.to_csv("tket_paper_config.csv", index=False)
    