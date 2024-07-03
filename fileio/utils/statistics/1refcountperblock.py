import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from plot_graph import plot_frame

def save_csv(df, filename, index=0):
    try:
        if index == 0:
            df.to_csv(filename, index=True, header=True, mode='w')  # encoding='utf-8-sig'
        else:  # append mode
            df.to_csv(filename, index=True, header=False, mode='a')  # encoding='utf-8-sig'
    except OSError:  # OSError: Cannot save file into a non-existent directory: '~'
        #if not os.path.exists(path):
        target_dir = filename.rfind('/')
        path = filename[:target_dir]
        os.makedirs(path)
        #---
        if index == 0:
            df.to_csv(filename, index=True, header=True, mode='w')  # encoding='utf-8-sig'
        else:  # append mode
            df.to_csv(filename, index=True, header=False, mode='a')  # encoding='utf-8-sig'


'''
##**blkdf1 = access count**
* x axis : unique block number
* y axis : access count per each block
'''

def ref_cnt(inputdf, concat=False):
    if (concat):
        df = inputdf.groupby(by=['blocknum', 'operation'], as_index=False).sum()
    else:
        df = inputdf.groupby(['blocknum', 'operation'])['blocknum'].count().reset_index(name='count')  # 'blockaddress'와 'type'을 기준으로 묶어서 세고, 이 이름은 'count'로

    return df

def ref_cnt_per_block(blkdf_list):
    df = pd.DataFrame()
    df_rw = pd.DataFrame()
    for i in range(len(blkdf_list)):
        cur_df = ref_cnt(blkdf_list[i], concat=False)
        df = pd.concat([df, cur_df])

    #group by type(read or write)
    df = ref_cnt(df, concat=True)

    #both read and write
    df_rw = df.groupby(by=['blocknum'], as_index=False).sum()
    df_rw['operation'] = 'read&write'

    df = pd.concat([df, df_rw], sort=True)
    return df

'''
**blkdf1 graph**
> Specify the axis range (manual margin adjustment required)
'''
def plot_ref_cnt_graph(blkdf, fig_title, filename):
    fig, ax = plot_frame((1, 1), (7, 4), title=fig_title, xlabel='unique block number', ylabel='access count', font_size=13)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='black', alpha=0.5, linestyle='--')

    # plot graph
    x1 = blkdf['blocknum'][(blkdf['operation'] == 'read')]
    x2 = blkdf['blocknum'][(blkdf['operation'] == 'write')]
    y1 = blkdf['count'][(blkdf['operation'] == 'read')]
    y2 = blkdf['count'][(blkdf['operation'] == 'write')]
    print(x1.max(), x2.max())
    print(y1.min(), y1.max())
    print(y2.min(), y2.max())

    plt.bar(x1, y1, color='blue', edgecolor='blue', label='read')
    plt.bar(x2, y2, color='red', edgecolor='red', label='write')

    # legend
    ax.legend(loc='upper right', ncol=1, fontsize=13)  # loc = 'best'

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)

if __name__=="__main__":
    # add parser
    parser = argparse.ArgumentParser(
        description="plot reference count per each block")

    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')
    parser.add_argument("--title", "-t", metavar='T', type=str,
                        nargs='?', default='', help='title of a graph')
    args = parser.parse_args()

    ## use list of chunk
    blkdf = pd.read_csv(args.input, sep=',', chunksize=1000000, header=0, index_col=0, on_bad_lines='skip')
    df1 = ref_cnt_per_block(blkdf_list=list(blkdf))
    save_csv(df1, args.output+'.csv', 0)

    #df1 = pd.read_csv(args.output+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')
    plot_ref_cnt_graph(blkdf=df1, fig_title=args.title, filename=args.output)
