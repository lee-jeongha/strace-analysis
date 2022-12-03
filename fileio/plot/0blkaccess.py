import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
blkdf["read_blk"] = blkdf["blocknum"]
blkdf["write_blk"] = blkdf["blocknum"]
blkdf.loc[(blkdf.operation != "read"), "read_blk"] = np.NaN
blkdf.loc[(blkdf.operation != "write"), "write_blk"] = np.NaN

blkdf.to_csv(args.output)

# plot graph
plt.rc('font', size=20)
fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
if args.title != '':
    plt.title(args.title, fontsize=20)

# scatter
x = blkdf['time_interval']
y1 = blkdf['read_blk']
y2 = blkdf['write_blk']

plt.scatter(x, y1, color='blue', label='read', s=3)  # aquamarine
plt.scatter(x, y2, color='red', label='write', s=3)  # salmon

# legend
fig.supxlabel('time(sec)', fontsize=25)
fig.supylabel('unique block number', fontsize=25)
ax.legend(loc='upper left', ncol=1, fontsize=20, markerscale=3)

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)
