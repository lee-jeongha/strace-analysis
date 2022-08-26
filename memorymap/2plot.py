import argparse
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')
parser.add_argument("--pid", "-p", metavar='P', type=str,
                    nargs='?', help='specify pid')
parser.add_argument("--title", "-t", metavar='T', type=str,
                    nargs='?', default='', help='title of a graph')
args = parser.parse_args()

# column
C_start_time = 0
C_end_time = 1
C_pid = 2
C_filename = 3
C_start_address = 4
C_end_address = 5

# calculate time_interval
def time_interval(start_timestamp, timestamp):
    start_time = [] # [hour, min, sec, usec]
    start_time.append(int(start_timestamp[:2]))
    start_time.append(int(start_timestamp[3:5]))
    start_time.append(int(start_timestamp[6:8]))
    start_time.append(int(start_timestamp[9:]))

    time = [] # [hour, min, sec, usec]
    time.append(int(timestamp[:2]))
    time.append(int(timestamp[3:5]))
    time.append(int(timestamp[6:8]))
    time.append(int(timestamp[9:]))

    # micro second
    if start_time[3] > time[3]:
        usec = (1000000 + time[3]) - start_time[3]
        time[2] -= 1
    else:
        usec = time[3] - start_time[3]

    # second
    if start_time[2] > time[2]:
        sec = (60 + time[2]) - start_time[2]
        time[1] -= 1
    else:
        sec = time[2] - start_time[2]
    
    # minute
    if start_time[1] > time[1]:
        min = (60 + time[1]) - start_time[1]
        time[0] -= 1
    else:
        min = time[1] - start_time[1]

    # hour
    if start_time[0] > time[0]:
        hour = (24 + time[0]) - start_time[0]
    else:
        hour = time[0] - start_time[0]
    
    return str(hour*3600 + min*60 + sec) + "." + '{0:>06d}'.format(usec)

# read logfile
#df = pd.read_csv(args.input, header=None, names=['start_time', 'end_time', 'pid', 'filename', 'start_address', 'end_address'], on_bad_lines='warn')
df = pd.read_csv(args.input, header=None, names=[0, 1, 2, 3, 4, 5], on_bad_lines='warn', dtype={4:'string', 5:'string'})

#---

base_time = df[0][0]
df[0] = df[0].apply(lambda x: time_interval(base_time, x))
df[1] = df[1].apply(lambda x: time_interval(base_time, x))

if args.pid:
    df = df[df[2].str.contains(args.pid) | (df[2]=='MAP_SHARED')]

digit_length_list = sorted(list(df[4].astype(int).unique()))
digit_length_partition = [digit_length_list[0],]
for digit_length in digit_length_list[1:]:
    if digit_length - digit_length_partition[-1] >= 1e6:
        digit_length_partition.append(digit_length)
digit_length_partition.append(int(digit_length_list[-1]) + 1)
#print("-----------digit length-------------", digit_length_partition)

df_heap = df[(df[3]=='HEAP_brk')]
df_stack = df[(df[3]=='STACK_mmap')]
df_anno = df[(df[3].isnull())]
df_mapped = df[(df[3]!='HEAP_brk') & (df[3]!='STACK_mmap') & (df[3].notnull())]

#---

plt.rc('font', size=15)
handles = [plt.Rectangle((0,0),1,1, color=color) for color in ['blue', 'red', 'green', 'yellow']]

if len(digit_length_partition) == 1:
    plt.xlabel('time', fontsize = 20)
    plt.ylabel('virtual memory block address', fontsize = 20)
    plt.legend(handles, ['stack', 'file mapping', 'annonymous mapping', 'heap'], fontsize=15, loc='upper right')

    for i in df_stack.index:
        plt.fill_between([float(df_stack[0][i]), float(df_stack[1][i])], int(df_stack[4][i]), int(df_stack[5][i]), alpha=0.5, facecolor='blue', lw=0.0)
    for i in df_mapped.index:
        plt.fill_between([float(df_mapped[0][i]), float(df_mapped[1][i])], int(df_mapped[4][i]), int(df_mapped[5][i]), alpha=0.5, facecolor='red', lw=0.0)
    for i in df_anno.index:
        plt.fill_between([float(df_anno[0][i]), float(df_anno[1][i])], int(df_anno[4][i]), int(df_anno[5][i]), alpha=0.5, facecolor='green', lw=0.0)
    for i in df_heap.index[1:]:
        plt.fill_between([float(df_heap[0][i]), float(df_heap[1][i])], int(df_heap[4][i]), int(df_heap[5][i]), alpha=0.5, facecolor='yellow', lw=0.0)

else:
    height_ratio_list = [2**i for i in range(len(digit_length_partition) - 1)]
    fig, ax = plt.subplots(len(digit_length_partition[:-1]), 1, figsize=(8, 4*len(digit_length_partition[:-1])), gridspec_kw={'height_ratios': height_ratio_list}, sharex=True)

    fig.supxlabel('time', fontsize = 20)
    fig.supylabel('virtual memory block address', fontsize = 20)
    fig.legend(handles, ['stack', 'file mapping', 'annonymous mapping', 'heap'], fontsize=15, loc='upper right')

    fig_idx = len(digit_length_partition[:-1]) - 1
    for idx in range(len(digit_length_partition))[1:]:
        for i in df_stack[(df_stack[4].astype(int)<digit_length_partition[idx]) & (df_stack[4].astype(int)>=digit_length_partition[idx-1])].index:
            ax[fig_idx].fill_between([float(df_stack[0][i]), float(df_stack[1][i])], int(df_stack[4][i]), int(df_stack[5][i]), alpha=0.5, facecolor='blue', lw=0.0)
        for i in df_mapped[(df_mapped[4].astype(int)<digit_length_partition[idx]) & (df_mapped[4].astype(int)>=digit_length_partition[idx-1])].index:
            ax[fig_idx].fill_between([float(df_mapped[0][i]), float(df_mapped[1][i])], int(df_mapped[4][i]), int(df_mapped[5][i]), alpha=0.5, facecolor='red', lw=0.0)
        for i in df_anno[(df_anno[4].astype(int)<digit_length_partition[idx]) & (df_anno[4].astype(int)>=digit_length_partition[idx-1])].index:
            ax[fig_idx].fill_between([float(df_anno[0][i]), float(df_anno[1][i])], int(df_anno[4][i]), int(df_anno[5][i]), alpha=0.5, facecolor='green', lw=0.0)
        for i in df_heap[(df_heap[4].astype(int)<digit_length_partition[idx]) & (df_heap[4].astype(int)>=digit_length_partition[idx-1])].index[1:]:
            ax[fig_idx].fill_between([float(df_heap[0][i]), float(df_heap[1][i])], int(df_heap[4][i]), int(df_heap[5][i]), alpha=0.5, facecolor='yellow', lw=0.0)
        
        #ax[fig_idx].ticklabel_format(useOffset=False, useMathText=True)
        ax[fig_idx].ticklabel_format(axis='y', style='plain', useOffset=False)
        fig_idx -= 1
    fig.subplots_adjust(top=0.95, left=0.25, bottom=0.05, right=0.95, hspace=0.0) # wspace=0.0

if args.title != '':
    plt.suptitle(args.title, fontsize = 25)

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)

#---

df_heap.to_csv(args.output[:-4]+'_heap.csv')
df_stack.to_csv(args.output[:-4]+'_stack.csv')
df_mapped.to_csv(args.output[:-4]+'_mapped.csv')
df_anno.to_csv(args.output[:-4]+'_anno.csv')