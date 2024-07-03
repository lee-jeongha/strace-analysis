import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from plot_graph import plot_frame

# plot graph
def plot_ref_addr_graph(blkdf, fig_title, filename):
    '''real_time'''
    fig, ax = plot_frame((1, 1), (8, 8), title=fig_title, xlabel='Time(sec)', ylabel='Unique block number', log_scale=False)
    ax.xaxis.set_major_locator(MaxNLocator(7))

    # scatter
    x1 = blkdf['time_interval'][(blkdf['operation']=='read')]
    x2 = blkdf['time_interval'][(blkdf['operation']=='write')]
    y1 = blkdf.loc[(blkdf['operation']=='read'), ['blocknum']]
    y2 = blkdf.loc[(blkdf['operation']=='write'), ['blocknum']]

    ax.scatter(x1, y1, color='blue', label='read', s=1)
    ax.scatter(x2, y2, color='red', label='write', s=1)

    # legend
    ax.legend(loc=(0.2, 1.01), ncol=2, fontsize=20, markerscale=10)  # loc='upper left'

    #plt.show()
    plt.savefig(filename+'_realtime.png', dpi=300)

    #-----
    '''logical_time_single'''
    fig, ax = plot_frame((1, 1), (8, 8), title=fig_title, xlabel='Logical time', ylabel='Unique block number', log_scale=False)
    ax.xaxis.set_major_locator(MaxNLocator(7))

    # scatter
    x1 = blkdf.index[(blkdf['operation']=='read')]
    x2 = blkdf.index[(blkdf['operation']=='write')]
    ax.scatter(x1, y1, color='blue', label='read', s=1)
    ax.scatter(x2, y2, color='red', label='write', s=1)

    # legend
    ax.legend(loc=(0.2, 1.01), ncol=2, fontsize=20, markerscale=10)  # loc='upper left'

    #plt.show()
    plt.savefig(filename+'_logicaltime.png', dpi=300)

if __name__=="__main__":
    # add parser
    parser = argparse.ArgumentParser(description="plot block access pattern")

    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')
    parser.add_argument("--title", "-t", metavar='T', type=str,
                        nargs='?', default='', help='title of a graph')
    args = parser.parse_args()

    # read logfile
    blkdf = pd.read_csv(args.input, header=0)

    plot_ref_addr_graph(blkdf=blkdf, fig_title=args.title, filename=args.output)
