import pandas as pd
import matplotlib.pyplot as plt

from utils import plot_frame
from utils import save_csv

'''
# access count
* x axis : unique block number
* y axis : access count per each block
'''

def ref_cnt_per_block(blkdf_list):
    df = pd.DataFrame()
    df_rw = pd.DataFrame()
    for i in range(len(blkdf_list)):
        cur_df = blkdf_list[i].groupby(['blocknum', 'operation'])['blocknum'].count().reset_index(name='count')
        df = pd.concat([df, cur_df])

    # reduce sum
    df = df.groupby(by=['blocknum', 'operation'], as_index=False).sum()

    # both read and write
    df_rw = df.groupby(by=['blocknum'], as_index=False).sum()
    df_rw['operation'] = 'read&write'

    df = pd.concat([df, df_rw], sort=True)
    return df

# Specify the axis range (manual margin adjustment required)
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

    ax.bar(x1, y1, color='blue', edgecolor='blue', label='read')
    ax.bar(x2, y2, color='red', edgecolor='red', label='write')

    # legend
    ax.legend(loc='upper right', ncol=1, fontsize=13)  # loc = 'best'

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)
