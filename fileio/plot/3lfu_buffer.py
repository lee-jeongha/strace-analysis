# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
from plt_frame import plot_frame
import heapq
import multiprocessing as mp
import math, time

class LFUCache(object):
    def __init__(self, max_cache_size):
        self.cache = {}  # {addr: acc_count}
        self.lfu_heap = [] # [(acc_count, addr), ...]
        self.max_cache_size = max_cache_size
        self.in_cache_size = 0
        self.fault_cnt = 0

    def get(self):
        return self.cache, self.in_cache_size

    def set(self, cache):
        self.cache = cache
        self.in_cache_size = len(cache)

        lfu_heap = []
        for key, value in cache.items():
            addr, acc_count = key, value
            lfu_heap.append((acc_count, addr))
        self.lfu_heap = heapq.heapify(lfu_heap)

    def heap_sort(self, idx):
        # if new node is larger than left child or right child
        left = idx * 2 + 1
        right = idx * 2 + 2
        s_idx = idx
        if (left < len(self.lfu_heap)) and (self.lfu_heap[s_idx][0] > self.lfu_heap[left][0]):
            s_idx = left

        if (right < len(self.lfu_heap)) and (self.lfu_heap[s_idx][0] > self.lfu_heap[right][0]):
            s_idx = right

        if s_idx != idx:
            self.lfu_heap[idx], self.lfu_heap[s_idx] = self.lfu_heap[s_idx], self.lfu_heap[idx]
            return self.heap_sort(s_idx)

    def reference(self, ref_address):
        if ref_address in self.cache.keys():
            idx = self.lfu_heap.index((self.cache[ref_address], ref_address))
            ref_cnt = self.cache[ref_address] + 1
            updates = (ref_cnt, ref_address)
            self.cache[ref_address] = ref_cnt
            self.lfu_heap[idx] = updates

            # if new node is larger than left child or right child
            self.heap_sort(idx)

            return idx  # not an exact rank

        else:
            self.fault_cnt += 1
            updates = (1, ref_address)
            self.cache[ref_address] = 1
            if len(self.cache) >= self.max_cache_size:
                #heapq.heapreplace(self.lfu_heap, updates)
                evicted = heapq.heappop(self.lfu_heap)
                _ = self.cache.pop(evicted[1], None)
            heapq.heappush(self.lfu_heap, updates)

            return -1


def access_to_lfu_buffer(df, lfu_cache):
    s_time = time.time()
    for index, row in df.iterrows():  ### one by one
        assert (row['operation'] == 'read' or row['operation'] == 'write')

        ### Increase readcnt/writecnt by matching block_rank
        acc_rank = lfu_cache.reference(row['blocknum'])

        if index % 1000000 == 0:
            e_time = time.time()
            print(index, ":", e_time - s_time)

    return lfu_cache


def buffer_simulation(df, cache_sizes, filename):
    fault_cnt = []

    for i in range(len(cache_sizes)):
        lfu_cache = LFUCache(max_cache_size = cache_sizes[i])
        lfu_cache = access_to_lfu_buffer(df, lfu_cache)
        fault_cnt.append(lfu_cache.fault_cnt)
        print(i, "buffer_simulation: cache_size", cache_sizes[i] , "done\t", fault_cnt[-1], sep=' ')

    df = pd.DataFrame.from_dict({'fault_cnt':fault_cnt, 'ref_cnt':[df.shape[0]]*len(cache_sizes), 'cache_size':cache_sizes})
    df.to_csv(filename+'-lfu_buffer_simulation.csv')
    
    return fault_cnt

def mp_buffer_simulation(idx, df, fault_cnt, ref_cnt, cache_sizes):
    cache_size = cache_sizes[idx]
    lfu_cache = LFUCache(max_cache_size = cache_size)
    lfu_cache = access_to_lfu_buffer(df, lfu_cache)
    fault_cnt[idx] = lfu_cache.fault_cnt
    ref_cnt[idx] = df.shape[0]
    print(idx, "buffer_simulation: cache_size", cache_size , "done\t", lfu_cache.fault_cnt, sep=' ')


#-----
def lfu_buffer_graph(cache_sizes, fault_rate, title, filename, xlim : list = None, ylim : list = None):
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
    plt.savefig(filename+'-lfu_buffer_simulation.png', dpi=300)

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="plot lfu graph from log file")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    try:
        blkdf = pd.read_csv(args.input + '.csv', sep=',', header=0, index_col=None, error_bad_lines=False)#on_bad_lines='skip')
    except FileNotFoundError:
        print("no file named:", args.input + '.csv')

    block_num = blkdf['blocknum'].max()
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
    f = open(args.output + '-lfu_buffer_simulation.csv', 'w')
    f.write('fault_cnt,ref_cnt,cache_size\n')
    for i in range(len(fault_cnt)):
        f.write(str(fault_cnt[i])+','+str(ref_cnt[i])+','+str(cache_sizes[i])+'\n')
    f.close()

    #===== single-processing =====#
    #fault_cnt = buffer_simulation(df=blkdf, cache_sizes=cache_sizes, filename=args.output)
    
    #===== =====#
    '''df_buf = pd.read_csv(args.output + '-lfu_buffer_simulation.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
    fault_cnt = df_buf['fault_cnt']; ref_cnt = df_buf['ref_cnt']; cache_sizes = df_buf['cache_size']'''

    #===== plot-graph =====#
    '''lfu_buffer_graph([i * 100 // len(cache_sizes) for i in range(1, len(cache_sizes)+1)], [i / blkdf.shape[0] * 100 for i in fault_cnt],
                     title=args.title, filename=args.output, ylim=[0,100])'''
