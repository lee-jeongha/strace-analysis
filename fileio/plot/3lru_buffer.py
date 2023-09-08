# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
from fileio.plot.load_and_save import save_json, load_json
from fileio.plot.plt_frame import plot_frame

class LRUCache(object):
    def __init__(self, max_cache_size=float("inf")):
        self.cache = []
        self.max_cache_size = max_cache_size
        self.in_cache_size = 0
        self.fault_cnt = 0

    def get(self):
        return self.cache, self.in_cache_size

    def set(self, cache):
        self.cache = cache
        self.in_cache_size = len(cache)

    def reference(self, ref_address):
        if ref_address in self.cache:
            rank = self.cache.index(ref_address)
            if rank == 0:
                return rank
            else:
                _ = self.cache.pop(rank)
                self.cache.insert(0, ref_address)
                return rank

        else:
            self.fault_cnt += 1
            if self.in_cache_size >= self.max_cache_size:
                self.evict()
            self.cache.insert(0, ref_address)
            self.in_cache_size += 1
            return -1

    def evict(self):
        _ = self.cache.pop()
        self.in_cache_size -= 1

def ref_cnt_by_realtime_ranking(df, read_lru_cache, write_lru_cache, read_cnt, write_cnt):
    lru_caches = {'read':read_lru_cache, 'write':write_lru_cache}
    ref_cnts = {'read':read_cnt, 'write':write_cnt}

    for index, row in df.iterrows():  ### one by one
        assert (row['operation'] == 'read' or row['operation'] == 'write')
    
        lru_cache = lru_caches[row['operation']]
        ref_cnt = ref_cnts[row['operation']]

        ### Increase readcnt/writecnt by matching block_rank
        acc_rank = lru_cache.reference(row['blocknum'])
        if acc_rank == -1:
            continue
        else:
            try:
                ref_cnt[acc_rank] += 1  # Increase [acc_rank]th element of readcnt by 1
            except IndexError:  # list index out of range
                for i in range(len(ref_cnt), acc_rank + 1):
                    ref_cnt.insert(i, 0)
                ref_cnt[acc_rank] += 1

    return read_lru_cache, write_lru_cache, read_cnt, write_cnt

def access_to_lru_buffer(df, lru_cache):
    read_fault = 0
    write_fault = 0

    for index, row in df.iterrows():  ### one by one
        assert (row['operation'] == 'read' or row['operation'] == 'write')

        ### Increase readcnt/writecnt by matching block_rank
        acc_rank = lru_cache.reference(row['blocknum'])

        if acc_rank == -1:
            if row['operation'] == 'read':
                read_fault += 1
            elif row['operation'] == 'write':
                write_fault += 1

    return lru_cache, read_fault, write_fault

"""##** tendency toward temporal locality**
* x axis : rank(temporal locality)
* y axis : access count per block
"""

def ref_cnt_simulation(df, filename):
    read_lru_cache = LRUCache();    write_lru_cache = LRUCache()
    read_block_rank = list();    write_block_rank = list()
    read_cnt = list();    write_cnt = list()

    '''filename = filename + '_ref_cnt_by_rank.json'
    saving_list = ['read_block_rank', 'write_block_rank', 'read_cnt', 'write_cnt']

    read_block_rank, write_block_rank, read_cnt, write_cnt = load_json(saving_list, filename)
    read_lru_cache.set(read_block_rank)
    write_lru_cache.set(write_block_rank)'''

    read_lru_cache, write_lru_cache, read_cnt, write_cnt = ref_cnt_by_realtime_ranking(df, read_lru_cache, write_lru_cache, read_cnt, write_cnt)
    read_block_rank, _ = read_lru_cache.get()
    write_block_rank, _ = write_lru_cache.get()

    savings = {'read_block_rank': read_block_rank,
                'write_block_rank': write_block_rank,
                'read_cnt': read_cnt,
                'write_cnt': write_cnt}
    filename = filename + '_ref_cnt_by_rank.json'
    save_json(savings, filename)

    return read_lru_cache, write_lru_cache, read_cnt, write_cnt

def buffer_simulation(df, cache_sizes, filename):
    fault_cnt, read_fault_cnt, write_fault_cnt = [], [], []

    for i in range(len(cache_sizes)):
        lru_cache = LRUCache(max_cache_size = cache_sizes[i])
        lru_cache, read_fault, write_fault = access_to_lru_buffer(df, lru_cache)
        fault_cnt.append(lru_cache.fault_cnt)
        read_fault_cnt.append(read_fault)
        write_fault_cnt.append(write_fault)
        print("buffer_simulation: cache_size", cache_sizes[i] , "done", sep=' ')

    df = pd.DataFrame.from_dict({'fault_cnt':fault_cnt, 'read_fault_cnt':read_fault_cnt, 'write_fault_cnt':write_fault_cnt})
    df.to_csv(filename+'_buffer_simulation.csv')
    
    return fault_cnt, read_fault_cnt, write_fault_cnt


"""##**plot graph**"""
def lru_ref_cnt_graph(read_cnt, write_cnt, title, filename, xlim : list = None, ylim : list = None):
    fig, ax = plot_frame((2, 1), title=title, xlabel='page ranking', ylabel='# of references', log_scale=True)
    
    if xlim:
        plt.setp(ax, xlim=xlim)
    if ylim:
        plt.setp(ax, ylim=ylim)

    #read
    x1 = range(1,len(read_cnt)+1)
    y1 = read_cnt

    #write
    x2 = range(1,len(write_cnt)+1)
    y2 = write_cnt

    # read graph
    ax[0].scatter(x1, y1, color='blue', label='read', s=5)
    ax[0].legend(loc='lower left', ncol=1, fontsize=20, markerscale=3)

    # write graph
    ax[1].scatter(x2, y2, color='red', label='write', s=5)
    ax[1].legend(loc='lower left', ncol=1, fontsize=20, markerscale=3)

    #plt.show()
    plt.savefig(filename+'_ref_cnt_by_rank.png', dpi=300)

def lru_buffer_graph(cache_sizes, fault_rate, title, filename, xlim : list = None, ylim : list = None):
    fig, ax = plot_frame((1, 1), title=title, xlabel='cahce size', ylabel='fault rate', log_scale=False)
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
    plt.savefig(filename+'_buffer_simulation.png', dpi=300)

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

    read_lru_cache, write_lru_cache, read_cnt, write_cnt = ref_cnt_simulation(blkdf, filename=args.output)
    lru_ref_cnt_graph(read_cnt, write_cnt, title=args.title, filename=args.output)

    block_num = blkdf['blocknum'].max()
    cache_sizes = [round(block_num / 10 * i) for i in range(1, 11)]
    fault_cnt, read_fault_cnt, write_fault_cnt = buffer_simulation(df=blkdf, cache_sizes=cache_sizes, filename=args.output)
    #df_buf = pd.read_csv(args.output + '_buffer_simulation.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
    #fault_cnt = df_buf['fault_cnt'];    read_fault_cnt = df_buf['read_fault_cnt'];    write_fault_cnt = df_buf['write_fault_cnt']
    lru_buffer_graph([i * 100 // len(cache_sizes) for i in range(1, len(cache_sizes)+1)], [i / blkdf.shape[0] * 100 for i in fault_cnt],
                     title=args.title, filename=args.output, ylim=[0,100])
