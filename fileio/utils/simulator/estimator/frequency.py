# -*- coding: utf-8 -*-
import argparse
import matplotlib.pyplot as plt
import pandas as pd
from multiprocessing import Process, Queue

from plot_graph import plot_frame
from load_and_save import save_json, load_json
from simulation_type import overall_rank_simulation, separately_rank_simulation, simulation_regardless_of_type

class FreqNode(object):
    def __init__(self, freq, ref_block, pre, nxt):
        self.freq = freq
        self.ref_block = ref_block
        self.pre = pre  # previous FreqNode
        self.nxt = nxt  # next FreqNode

    def count_blocks(self):
        return len(self.ref_block)

    def remove(self):
        if self.pre is not None:
            self.pre.nxt = self.nxt
        if self.nxt is not None:
            self.nxt.pre = self.pre

        pre = self.pre
        nxt = self.nxt
        self.pre = self.nxt = None

        return (pre, nxt)

    def remove_block(self, ref_address): # remove ref_address from ref_block within freq_node
        ref_address_idx = self.ref_block.index(ref_address)
        _ = self.ref_block.pop(ref_address_idx)

        return ref_address_idx

    def insert_ref_block(self, ref_address):
        self.ref_block.insert(0, ref_address)

    def append_ref_block(self, ref_address):
        self.ref_block.append(ref_address)

    def insert_after_me(self, freq_node):
        freq_node.pre = self
        freq_node.nxt = self.nxt

        if self.nxt is not None:
            self.nxt.pre = freq_node
        else:
            self.nxt = None

        self.nxt = freq_node

    def insert_before_me(self, freq_node):
        if self.pre is not None:
            self.pre.nxt = freq_node

        freq_node.pre = self.pre
        freq_node.nxt = self
        self.pre = freq_node


class LFUCache(object):
    def __init__(self):
        self.cache = {}  # {addr: freq_node}
        self.freq_link_head = None

    def get(self):
        ref_table = {}  # {freq: [ref_block]}
        current = self.freq_link_head

        while current != None:
            freq = current.freq
            ref_block = current.ref_block
            ref_table[freq] = ref_block
            current = current.nxt

        return ref_table

    def set(self, ref_table):
        freqs = list(ref_table.keys())
        freqs.sort()

        prev_freq_node = None
        for freq in freqs:
            ref_block = ref_table[freq]
            target_freq_node = FreqNode(freq, ref_block, None, None)

            if prev_freq_node == None:
                self.freq_link_head = target_freq_node
            else:
                target_freq_node.pre = prev_freq_node
                prev_freq_node.nxt = target_freq_node

            for ref_addr in ref_block:
                self.cache[ref_addr] = target_freq_node

            prev_freq_node = target_freq_node

    def reference(self, ref_address):
        if ref_address in self.cache:
            freq_node = self.cache[ref_address]
            rank = self.get_freqs_rank(freq_node)
            #rank += freq_node.ref_block.index(ref_address)

            new_freq_node = self.move_next_to(ref_address, freq_node)
            self.cache[ref_address] = new_freq_node

            return rank
        
        else:
            new_freq_node = self.create_freq_node(ref_address)
            self.cache[ref_address] = new_freq_node
            
            return -1

    def move_next_to(self, ref_address, freq_node):  # for each access
        if freq_node.nxt is None or freq_node.nxt.freq != freq_node.freq + 1:
            target_freq_node = FreqNode(freq_node.freq + 1, list(), None, None)
            target_empty = True

        else:
            target_freq_node = freq_node.nxt
            target_empty = False

        target_freq_node.insert_ref_block(ref_address)

        if target_empty:
            freq_node.insert_after_me(target_freq_node)

        _ = freq_node.remove_block(ref_address)

        if freq_node.count_blocks() == 0: # if there is nothing left in freq_node
            if self.freq_link_head == freq_node:
                self.freq_link_head = target_freq_node

            freq_node.remove()
        
        return target_freq_node

    def create_freq_node(self, ref_address):
        ref_block = [ref_address]

        if self.freq_link_head is None or self.freq_link_head.freq != 1:
            new_freq_node = FreqNode(1, ref_block, None, None)
            self.cache[ref_address] = new_freq_node

            if self.freq_link_head is not None: # LFU has freq_link_head but frequency is not 1
                self.freq_link_head.insert_before_me(new_freq_node)

            self.freq_link_head = new_freq_node
            
            return new_freq_node

        else: # if LFU has freq_link_head which frequency value is 1
            self.freq_link_head.append_ref_block(ref_address)
        
            return self.freq_link_head
    
    def get_freqs_rank(self, freq_node):
        current = freq_node.nxt
        rank = 0

        while current != None:
            rank += current.count_blocks()
            current = current.nxt

        return rank


"""##**memdf5 = tendency toward temporal frequency**
* x axis : rank(temporal frequency)
* y axis : access count per block
"""

## load separate .csv file
def lfu_simulation(startpoint, endpoint_q, input_filename, output_filename, operation='all'):
    ref_block = LFUCache()
    block_rank = list()
    ref_cnt = list()
    
    if (startpoint > 0):
        filename = output_filename + "-" + operation + "_checkpoint" + str(startpoint - 1) + ".json"
        saving_list = ['block_rank', 'ref_cnt']

        block_rank, ref_cnt = load_json(saving_list, filename)
        ref_block.set(block_rank)
        # print(block_rank, ref_cnt)

    i = startpoint
    while True:
        if not startpoint:
            memdf = pd.read_csv(input_filename + '.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
        else:
            try:
                memdf = pd.read_csv(input_filename + '_' + str(i) + '.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')
            except FileNotFoundError:
                print("no file named:", input_filename + '_' + str(i) + '.csv')
                break

        if operation == 'read':
            memdf = memdf[memdf['operation'] == 'read']
        elif operation == 'write':
            memdf = memdf[memdf['operation'] == 'write']
        else:
            #print("choose operation 'read' or 'write'")
            #return
            pass

        ref_block, ref_cnt = simulation_regardless_of_type(memdf, ref_block, ref_cnt)
        block_rank = ref_block.get()

        if not startpoint:
            filename = output_filename + "-" + operation + ".json"
        else:
            filename = output_filename + "-" + operation + "_checkpoint" + str(i) + ".json"
        savings = {'block_rank': block_rank, 'ref_cnt': ref_cnt}
        save_json(savings, filename)

        if not startpoint:
            break
        else:
            i += 1
    endpoint_q.put(i)    # return i


"""##**memdf5 graph**"""
def lfu_graph(read_cnt, write_cnt, total_cnt, title, filename, xlim : list = None, ylim : list = None):
    fig, ax = plot_frame((2, 1), title=title, xlabel='File block rank', ylabel='Reference counts', log_scale=True)
    for a in ax:
        a.set_axisbelow(True)
        a.grid(True, which='major', color='black', alpha=0.5, linestyle='--')
        a.grid(True, which='minor', color='black', alpha=0.3, linestyle='--', lw=0.3)

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

    #total
    x3 = range(1,len(total_cnt)+1)
    y3 = total_cnt

    ax[0].scatter(x1, y1, color='blue', alpha=0.5, label='read', s=20)    # read graph
    ax[0].scatter(x2, y2, color='red', alpha=0.5, label='write', s=20)    # write graph
    ax[1].scatter(x3, y3, color='green', alpha=0.5, label='read&write', s=20)    # total graph

    # legend    
    for a in ax:
        a.legend(loc='upper right', ncol=1, fontsize=20, markerscale=3)

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="plot lfu graph from log file")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--start_chunk", "-s", metavar='S', type=int, nargs='?', default=0,
                        help='start chunk index')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    endpoint_q = Queue()
    processes = []
    operations = ['read', 'write', 'all']
    endpoints, ref_cnts = [], []

    for op in operations:
        p = Process(target=lfu_simulation, args=(args.start_chunk, endpoint_q, args.input, args.output, op))
        processes.append(p)
        p.start()

    # get return value
    for p in processes:
        endpoints.append(endpoint_q.get())

    for p in processes:
        p.join()

    if not args.start_chunk:
        suffix = ".json"
    else:
        end_chunk = endpoints[0]
        suffix = "_checkpoint" + str(end_chunk) + ".json"

    for op in operations:
        filename = args.output + "-" + op + suffix
        block_rank, ref_cnt = load_json(['block_rank', 'ref_cnt'], filename)
        ref_cnts.append(ref_cnt)
    lfu_graph(read_cnt=ref_cnts[0], write_cnt=ref_cnts[1], total_cnt=ref_cnts[2], title=args.title, filename=args.output)
