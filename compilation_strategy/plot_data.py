import matplotlib.pyplot as plt
import numpy as np
import pandas
import seaborn as sns

for encoding in ("JW", "BK", "P"):
    filename = "results/{}_results".format(encoding)

    table_initial = pandas.read_csv("{}.csv".format(filename))
    if encoding == "JW":
        table_TLOS = pandas.read_csv("results/TLOS_results.csv")
    for metric in ("Count", "Depth"):

        list_spins = table_initial["Active Spin Orbitals"]
        list_uncoloured = table_initial["Naive CX {}".format(metric)]
        list_pair = table_initial["Pairwise CX {}".format(metric)]
        list_set = table_initial["Set CX {}".format(metric)]
        if encoding == "JW":
            list_template = table_TLOS["TLOS CX {}".format(metric)]
        name = "CX {}".format(metric)

        all_lists = [list_uncoloured, list_pair, list_set]
        if encoding == "JW":
            all_lists.append(list_template)

        for l in all_lists:
            reduction_list = [1 - l[i] / list_uncoloured[i] for i in range(len(l))]
            print(
                "{} {} maximum reduction: {}".format(
                    encoding, metric, max(reduction_list)
                )
            )
            reduction = sum(reduction_list) / len(l)
            print("{} {} average reduction: {}".format(encoding, metric, reduction))
        f, (ax1) = plt.subplots(1, 1)

        markers = ["v", "p", "x", "."]
        colours = sns.color_palette("Set2")
        strat = ["Naive", "Pairwise", "Sets", "TLOS"]
        linestyles = [":", "--", "-.", "-"]
        d = 4
        for i, l in enumerate(all_lists):
            ax1.plot(
                list_spins,
                l,
                label=strat[i],
                marker=markers[i],
                markersize=6,
                c=colours[i],
                linewidth=0,
            )
            ax1.plot(
                list_spins,
                10 ** (np.poly1d(np.polyfit(list_spins, np.log10(l), d))(list_spins)),
                linewidth=1.1,
                linestyle=linestyles[i],
                c=colours[i],
            )

        ax1.set_yscale("log")
        ax1.set_xlabel("Active Spin Orbitals")
        ax1.set_ylabel("{}".format(name))

        handles, labels = ax1.get_legend_handles_labels()
        plt.legend(
            handles=handles,
            labels=labels,
            loc="upper left",
            ncol=2,
            title="Strategy",
            fancybox=True,
            handlelength=1,
            markerscale=1.3,
        )
        f.set_size_inches(6, 5, forward=True)
        stat = name.replace(" ", "_")
        plt.savefig(
            "plots/Compare_{}_{}.eps".format(encoding, stat), format="eps", dpi=1000
        )
