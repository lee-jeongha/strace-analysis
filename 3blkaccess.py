import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# add parser
parser = argparse.ArgumentParser(description="refine for read,write,lseek,pread64,pwrite64")

parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt', help='output file')
args = parser.parse_args()

# read logfile
blkdf4 = pd.read_csv(args.input, header=0)

# separate read/write
blkdf4["read_blk"] = blkdf4["blocknum"]
blkdf4["write_blk"] = blkdf4["blocknum"]
blkdf4.loc[(blkdf4.operation != "read"), "read_blk"] = np.NaN
blkdf4.loc[(blkdf4.operation != "write"), "write_blk"] = np.NaN

blkdf4.to_csv(args.output)

# plot graph
#plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 10)
#plt.rcParams['font.size'] = 12

# scatter
x = blkdf4['time']
y1 = blkdf4['read_blk']
y2 = blkdf4['write_blk']

plt.scatter(x, y1, color='blue', label='read', s=5) #aquamarine
plt.scatter(x, y2, color='red', label='write', s=5) #salmon

# legend
plt.xlabel('real time')
plt.ylabel('unique block number')
plt.legend(loc='upper right', ncol=1) #loc = 'best'
#plt.margins(x=5)

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)
