# -*- coding: utf-8 -*-
import argparse
import matplotlib.pyplot as plt
import pandas as pd
from multiprocessing import Process, Queue

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from plot_graph import plot_frame
from load_and_save import save_json, load_json
from simulation_type import overall_rank_simulation, separately_rank_simulation, simulation_regardless_of_type

class LRUCache(object):
    def __init__(self):
        self.cache = []

    def get(self):
        ref_table = self.cache
        return ref_table

    def set(self, ref_table):
        self.cache = ref_table

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
            self.cache.insert(0, ref_address)
            return -1


'''tendency toward temporal locality'''

## load separate .csv file
def recency_estimator_simulation(startpoint, endpoint_q, input_filename, output_filename, operation='all'):
    ref_block = LRUCache()
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

## plot graph
def recency_estimator_graph(read_cnt, write_cnt, total_cnt, title, filename, xlim : list = None, ylim : list = None):
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
    parser = argparse.ArgumentParser(description="Evaluate the efficiency of recency estimators from log file")
    parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt',
                        help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    parser.add_argument("--start_chunk", "-s", metavar='S', type=int, nargs='?', default=None,
                        help='start chunk index')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    endpoint_q = Queue()
    processes = []
    operations = ['read', 'write', 'all']
    endpoints, ref_cnts = [], []

    if not args.start_chunk:
        suffix = "-recency_estimator_simulation"
    else:
        end_chunk = endpoints[0]
        suffix = "_checkpoint" + str(end_chunk) + "-recency_estimator_simulation"

    for op in operations:
        p = Process(target=recency_estimator_simulation, args=(args.start_chunk, endpoint_q, args.input, args.output+suffix, op))
        processes.append(p)
        p.start()

    # get return value
    for p in processes:
        endpoints.append(endpoint_q.get())

    for p in processes:
        p.join()

    for op in operations:
        filename = args.output + suffix + "-" + op + ".json"
        _, ref_cnt = load_json(['block_rank', 'ref_cnt'], filename)
        ref_cnts.append(ref_cnt)
    recency_estimator_graph(read_cnt=ref_cnts[0], write_cnt=ref_cnts[1], total_cnt=ref_cnts[2], title=args.title, filename=args.output+suffix)

