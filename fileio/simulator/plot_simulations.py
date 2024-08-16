# -*- coding: utf-8 -*-
import argparse
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as mtick
import pandas as pd

from utils import plot_frame
from utils import save_json, load_json

def estimator_graph_by_operation(read_cnt, write_cnt, total_cnt, title, filename, xlim : list = None, ylim : list = None):
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

def _buffer_cache_graph(cache_sizes, fault_rate, title, filename, xlim : list = None, ylim : list = None):
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
    plt.savefig(filename+'.png', dpi=300)

def estimator_graph(recency_cnt, frequency_cnt, title, filename, xlim : list = None, ylim : list = None):
    #fig, ax = plot_frame((1, 1), title=title, xlabel='File block rank', ylabel='Reference counts', log_scale=True)
    fig, ax = plot_frame((1, 1), title=title, xlabel='File block rank', ylabel='Reference counts', log_scale=False)
    ax.set_axisbelow(True)
    ax.grid(True, which='major', color='black', alpha=0.5, linestyle='--')
    ax.grid(True, which='minor', color='black', alpha=0.3, linestyle='--', lw=0.3)
    #ax.grid(axis='y', which='minor', color='black', alpha=0.3, linestyle='--', lw=0.3)
    plt.xscale('log')
    plt.yscale('log')

    if xlim:
        plt.setp(ax, xlim=xlim)
    if ylim:
        plt.setp(ax, ylim=ylim)

    #recency
    x1 = range(1,len(recency_cnt)+1)
    y1 = recency_cnt

    #frequency
    x2 = range(1,len(frequency_cnt)+1)
    y2 = frequency_cnt

    # colors: ['royalblue', 'crimson'], ['#006b70', '#ff7c00'], ['purple', 'darkgreen']
    ax.scatter(x1, y1, color='#006b70', alpha=0.7, marker='o', label='recency')       # recency graph
    ax.scatter(x2, y2, color='#ff7c00', alpha=0.7, marker='s', label='frequency')     # frequency graph

    # legend
    ax.legend(loc=(0.075, 1.01), ncol=2, fontsize=20, markerscale=3)  # loc='upper right', ncol=1

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)

def buffer_cache_graph(lru_df, lfu_df, title, filename):
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
