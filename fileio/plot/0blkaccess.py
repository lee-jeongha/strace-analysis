import argparse
import pandas as pd
import matplotlib.pyplot as plt

# plot graph
def plot_ref_addr_graph(blkdf, filename):
    plt.rc('font', size=20)
    fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
    if args.title != '':
        plt.title(args.title, fontsize=20)

    # scatter
    x1 = blkdf['time_interval'][(blkdf['operation']=='read')]
    x2 = blkdf['time_interval'][(blkdf['operation']=='write')]
    y1 = blkdf.loc[(blkdf['operation']=='read'), ['blocknum']]
    y2 = blkdf.loc[(blkdf['operation']=='write'), ['blocknum']]

    plt.scatter(x1, y1, color='blue', label='read', s=1)  # aquamarine
    plt.scatter(x2, y2, color='red', label='write', s=1)  # salmon

    # legend
    fig.supxlabel('time(sec)', fontsize=25)
    fig.supylabel('unique block number', fontsize=25)
    ax.legend(loc='upper left', ncol=1, fontsize=20, markerscale=3)

    #plt.show()
    plt.savefig(filename+'_realtime.png', dpi=300)

    plt.cla()
    x1 = blkdf.index[(blkdf['operation']=='read')]
    x2 = blkdf.index[(blkdf['operation']=='write')]
    plt.scatter(x1, y1, color='blue', label='read', s=1)  # aquamarine
    plt.scatter(x2, y2, color='red', label='write', s=1)  # salmon

    # legend
    fig.supxlabel('logical time', fontsize=25)
    fig.supylabel('unique block number', fontsize=25)
    ax.legend(loc='upper left', ncol=1, fontsize=20, markerscale=3)

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

    # separate read/write
    '''blkdf["read_blk"] = blkdf["blocknum"]
    blkdf["write_blk"] = blkdf["blocknum"]
    blkdf.loc[(blkdf.operation != "read"), "read_blk"] = np.NaN
    blkdf.loc[(blkdf.operation != "write"), "write_blk"] = np.NaN

    blkdf.to_csv(args.output)'''

    plot_ref_addr_graph(blkdf=blkdf, filename=args.output)
