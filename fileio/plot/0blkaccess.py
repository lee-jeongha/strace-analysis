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
blkdf3 = pd.read_csv(args.input, header=0)

# separate read/write
blkdf3["read_blk"] = blkdf3["blocknum"]
blkdf3["write_blk"] = blkdf3["blocknum"]
blkdf3.loc[(blkdf3.operation != "read"), "read_blk"] = np.NaN
blkdf3.loc[(blkdf3.operation != "write"), "write_blk"] = np.NaN

blkdf3.to_csv(args.output)

# plot graph
#plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 10)
plt.rcParams['font.size'] = 17

if args.title != '':
    plt.title(args.title, fontsize=20)

# scatter
x = blkdf3['time_interval']
y1 = blkdf3['read_blk']
y2 = blkdf3['write_blk']

plt.scatter(x, y1, color='blue', label='read', s=5)  # aquamarine
plt.scatter(x, y2, color='red', label='write', s=5)  # salmon

# legend
plt.xlabel('real time')
plt.ylabel('unique block number')
plt.legend(loc='upper right', ncol=1)  # loc = 'best'
#plt.margins(x=5)

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)
