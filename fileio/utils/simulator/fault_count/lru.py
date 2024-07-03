# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np
from functools import lru_cache
from plot_graph import plot_frame
import multiprocessing as mp
import math, time

#-----
def buffer_simulation(df, cache_sizes, filename):
    cache_info = []

    for i in range(len(cache_sizes)):
        @lru_cache(maxsize=cache_sizes[i])
        def access_cache(blocknum):
            return 1

        for index, row in df.iterrows():  ### one by one
            access_cache(row['blocknum'])

        cache_info.append(access_cache.cache_info())
        print("buffer_simulation: cache_size", cache_sizes[i] , "done\t", cache_info[-1], sep=' ')
        access_cache.cache_clear()

    cache_info = np.array(cache_info)
    df = pd.DataFrame.from_dict({'fault_cnt':cache_info[:,1], 'ref_cnt':[df.shape[0]]*len(cache_sizes), 'cache_size':cache_sizes})
    df.to_csv(filename+'-lru_buffer_simulation.csv')
    
    return cache_info[:,1]

def mp_buffer_simulation(idx, df, fault_cnt, ref_cnt, cache_sizes):
    cache_size = cache_sizes[idx]

    @lru_cache(maxsize=cache_size)
    def access_cache(blocknum):
        return 1

    for index, row in df.iterrows():  ### one by one
        access_cache(row['blocknum'])

    cache_info = access_cache.cache_info()
    fault_cnt[idx] = cache_info[1]
    ref_cnt[idx] = df.shape[0]

    print(idx, "buffer_simulation: cache_size", cache_size , "done\t", cache_info[1], sep=' ')
    access_cache.cache_clear()

#-----
def lru_buffer_graph(cache_sizes, fault_rate, title, filename, xlim : list = None, ylim : list = None):
    fig, ax = plot_frame((1, 1), title=title, xlabel='Buffer size (%)', ylabel='Fault ratio (%)', log_scale=False)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())

    if xlim:
        plt.setp(ax, xlim=xlim)
    if ylim:
        plt.setp(ax, ylim=ylim)

    x = cache_sizes
    y = fault_rate

    ax.plot(x, y, color='purple', label='fault rate', lw=3, marker="o", ms=12)
    ax.legend(loc='lower left', ncol=1, fontsize=20)

    #plt.show()
    plt.savefig(filename+'-lru_buffer_simulation.png', dpi=300)

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="plot lru graph from log file")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    try:
        blkdf = pd.read_csv(args.input + '.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
    except FileNotFoundError:
        print("no file named:", args.input + '.csv')

    block_num = blkdf['blocknum'].max() + 1    # DataFrame index starts from 0
    cache_sizes = [round(block_num / 10 * i) for i in range(1, 10)]

    #===== multiprocessing =====#
    n_nodes = len(cache_sizes);    p_num = 3;    processes = []
    fault_cnt = mp.Array('i', range(n_nodes));    ref_cnt = mp.Array('i', range(n_nodes));    max_size = mp.Array('i', range(n_nodes))

    for i in range(math.ceil(n_nodes/p_num)):
        for j in range(p_num):
            if ((i * p_num + j) >= n_nodes):
                break
            print("start process:", (i * p_num + j))
            process = mp.Process(target=mp_buffer_simulation, args=(i * p_num + j, blkdf, fault_cnt, ref_cnt, cache_sizes))
            processes.append(process)
            process.start()
        
        for p in processes:
            p.join()
    print(fault_cnt[:])
    f = open(args.output + '-lru_buffer_simulation.csv', 'w')
    f.write('fault_cnt,ref_cnt,cache_size,block_num\n')
    for i in range(len(fault_cnt)):
        f.write(str(fault_cnt[i])+','+str(ref_cnt[i])+','+str(cache_sizes[i])+','+str(block_num)+'\n')
    f.close()

    #===== single-processing =====#
    #fault_cnt = buffer_simulation(df=blkdf, cache_sizes=cache_sizes, filename=args.output)

    #===== =====#
    '''df_buf = pd.read_csv(args.output + '-lru_buffer_simulation.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
    fault_cnt = df_buf['fault_cnt']; ref_cnt = df_buf['ref_cnt'];   cache_sizes = df_buf['cache_size']'''

    #===== plot-graph =====#
    '''lru_buffer_graph([i * 100 // len(cache_sizes) for i in range(1, len(cache_sizes)+1)], [i / blkdf.shape[0] * 100 for i in miss_cnt],
                     title=args.title, filename=args.output, ylim=[0,100])'''
