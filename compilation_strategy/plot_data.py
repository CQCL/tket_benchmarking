import matplotlib.pyplot as plt
import numpy as np
import pandas
import seaborn as sns

for encoding in ('JW', 'BK', 'P'):
    for depth in (True, False): # either plot CX Depth or CX Count
        filename = '{}_results'.format(encoding)

        table_initial = pandas.read_csv('{}.csv'.format(filename))
        if encoding == 'JW':
            table_TLOS = pandas.read_csv('TLOS_results.csv')

        if depth:
            list_spins = table_initial['Active Spin Orbitals']
            list_uncoloured = table_initial['Naive CX Depth']
            list_pair = table_initial['Pairwise CX Depth']
            list_set = table_initial['Set CX Depth']
            if encoding == 'JW':
                list_template = table_TLOS['TLOS CX Depth']
            name = 'CX depth'
        else:
            list_spins = table_initial['Active Spin Orbitals']
            list_uncoloured = table_initial['Naive CX Count']
            list_pair = table_initial['Pairwise CX Count']
            list_set = table_initial['Set CX Count']
            if encoding == 'JW':
                list_template = table_TLOS['TLOS CX Count']
            name = 'CX count'

        all_lists = [list_uncoloured,list_pair,list_set]
        if encoding == 'JW':
            all_lists.append(list_template)

        for l in all_lists:
            reduction = 1-sum([l[i]/list_uncoloured[i] for i in range(len(list_uncoloured))])/len(list_uncoloured)
            print(reduction)
        f, (ax1) = plt.subplots(1,1)


        markers = ['v','p','x','.']
        colours = sns.color_palette('Set2')
        names = ['Naive','Pairwise','Sets','TLOS']
        linestyles = [':','--','-.','-']
        d = 4
        for i, l in enumerate(all_lists) :
            ax1.plot(list_spins,l,label=names[i],marker=markers[i],markersize=6,c=colours[i],linewidth=0)
            ax1.plot(list_spins, 10**(np.poly1d(np.polyfit(list_spins,np.log10(l), d))(list_spins)),linewidth=1.1,linestyle=linestyles[i],c=colours[i])

        ax1.set_yscale('log')
        ax1.set_xlabel('Active Spin Orbitals')
        ax1.set_ylabel('{}'.format(name))

        handles, labels = ax1.get_legend_handles_labels()
        plt.legend(handles=handles,labels=labels,loc='upper left',ncol=2,title='Strategy',fancybox=True,handlelength=1,markerscale=1.3)
        f.set_size_inches(6,5,forward=True)
        stat = name.replace(' ', '_')
        plt.savefig('plots/Compare_{}_{}.eps'.format(encoding,stat), format='eps', dpi=1000)