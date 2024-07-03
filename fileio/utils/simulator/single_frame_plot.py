# -*- coding: utf-8 -*-

from matplotlib.ticker import MaxNLocator
import argparse
import matplotlib.pyplot as plt
import pandas as pd

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from plot_graph import plot_frame
from load_and_save import save_json, load_json

def estimator_graph(lru_cnt, lfu_cnt, title, filename, xlim : list = None, ylim : list = None):
    fig, ax = plot_frame((1, 1), title=title, xlabel='File block rank', ylabel='Reference counts', log_scale=True)
    ax.set_axisbelow(True)
    ax.grid(True, which='major', color='black', alpha=0.5, linestyle='--')
    ax.grid(True, which='minor', color='black', alpha=0.3, linestyle='--', lw=0.3)
    
    if xlim:
        plt.setp(ax, xlim=xlim)
    if ylim:
        plt.setp(ax, ylim=ylim)

    #recency
    x1 = range(1,len(lru_cnt)+1)
    y1 = lru_cnt

    #frequency
    x2 = range(1,len(lfu_cnt)+1)
    y2 = lfu_cnt

    # colors: ['royalblue', 'crimson'], ['#006b70', '#ff7c00']
    ax.scatter(x1, y1, color='#006b70', alpha=0.7, marker='o', label='recency')       # recency graph
    ax.scatter(x2, y2, color='#ff7c00', alpha=0.7, marker='s', label='frequency')     # frequency graph

    # legend
    ax.legend(loc=(0.075, 1.01), ncol=2, fontsize=20, markerscale=3)  # loc='upper right', ncol=1

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)

def fault_cnt_graph(lru_df, lfu_df, title, filename):
    fig, ax = plot_frame((1, 1), title=title, xlabel='Buffer size (%)', ylabel='Hit ratio (%)', log_scale=False)
    ax.set_axisbelow(True)
    ax.grid(True, which='major', color='black', alpha=0.5, linestyle='--')
    ax.xaxis.set_major_locator(MaxNLocator(6))
    ax.yaxis.set_major_locator(MaxNLocator(6))

    plt.setp(ax, xlim=[0, 102])
    plt.setp(ax, ylim=[0, 102])

    buffer_size = list(range(10, 100, 10)) + [100]
    unq_reference = (lru_df['block_num'][0]/lru_df['ref_cnt'][0])

    y1 = (lru_df['fault_cnt']/lru_df['ref_cnt']).to_list() + [unq_reference]    #lru
    y2 = (lfu_df['fault_cnt']/lfu_df['ref_cnt']).to_list() + [unq_reference]    #lfu

    # hit_ratio
    y1 = [(1 - y) * 100 for y in y1]
    y2 = [(1 - y) * 100 for y in y2]

    ax.plot(buffer_size, y1, color='#006b70', alpha=0.7, marker='o', markersize=15, label='LRU')      # lru graph
    ax.plot(buffer_size, y2, color='#ff7c00', alpha=0.7, marker='s', markersize=15, label='LFU')      # lfu graph

    # legend
    ax.legend(loc=(0.15, 1.01), ncol=2, fontsize=20, markerscale=1.2)  # loc='lower right', ncol=1

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)

#-----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="plot lfu graph from log file")
    parser.add_argument("--lru_input", "-r", metavar='R', type=str, nargs='?', default='lru_input.json',
                        help='LRU input file')
    parser.add_argument("--lfu_input", "-f", metavar='F', type=str, nargs='?', default='lfu_input.json',
                        help='LFU input file')
    parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt',
                        help='output file')
    #parser.add_argument("--end_chunk", "-e", metavar='E', type=int, nargs='?', default=None,
    #                    help='end chunk index')
    parser.add_argument("--suffix", "-s", metavar='S', type=str, nargs='?', default=None,
                        help='file name suffix')
    parser.add_argument("--graph", "-g", metavar='G', type=str, nargs='?', default='estimator',
                        help='graph type. choose between estimator/faultcnt')
    parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='',
                        help='title of a graph')
    args = parser.parse_args()

    if args.graph == 'estimator':
        if not args.suffix:
            suffix = "_estimator_simulation-all"
        else:
            suffix = args.suffix    # "_checkpoint" + str(end_chunk) + ".json"

        lru_filename = args.lru_input + '-recency' + suffix + '.json'
        _, lru_ref_cnt = load_json(['block_rank', 'ref_cnt'], lru_filename)

        lfu_filename = args.lfu_input + '-frequency' + suffix + '.json'
        _, lfu_ref_cnt = load_json(['block_rank', 'ref_cnt'], lfu_filename)

        estimator_graph(lru_cnt=lru_ref_cnt, lfu_cnt=lfu_ref_cnt, title=args.title, filename=args.output)

    elif args.graph == 'faultcnt':
        if not args.suffix:
            suffix = "_faultcnt_simulation"
        else:
            suffix = args.suffix

        lru_filename = args.lru_input + '-lru' + suffix + '.csv'
        lru_df = pd.read_csv(lru_filename)

        lfu_filename = args.lfu_input + '-lfu' + suffix + '.csv'
        lfu_df = pd.read_csv(lfu_filename)

        fault_cnt_graph(lru_df=lru_df, lfu_df=lfu_df, title=args.title, filename=args.output)
