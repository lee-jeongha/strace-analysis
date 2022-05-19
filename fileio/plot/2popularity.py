import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# add parser
parser = argparse.ArgumentParser(description="plot popularity graph")

parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt', help='output file')
args = parser.parse_args()

def save_csv(df, filename, index=0):
  try:
    if index==0:
      df.to_csv(filename, index=True, header=True, mode='w') # encoding='utf-8-sig'
    else: #append mode
      df.to_csv(filename, index=True, header=False, mode='a') # encoding='utf-8-sig'
  except OSError:	# OSError: Cannot save file into a non-existent directory: '~'
    #if not os.path.exists(path):
    target_dir = filename.rfind('/')
    path = filename[:target_dir]
    os.mkdir(path)
    #---
    if index==0:
      df.to_csv(filename, index=True, header=True, mode='w') # encoding='utf-8-sig'
    else: #append mode
      df.to_csv(filename, index=True, header=False, mode='a') # encoding='utf-8-sig'

"""##**blkdf2 = tendency of memory block access**
**blkdf2.1**
* x axis : ranking by references count
* y axis : reference count

**blkdf2.2**
* x axis : ranking by % of reference count (in percentile form)
* y axis : % of reference count
"""

memdf2 = pd.read_csv(args.input, sep=',', header=0, index_col=0, on_bad_lines='skip')
memdf2_rw = pd.read_csv(args.input[:-4]+'_rw.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')

# ranking
memdf2['read_rank'] = memdf2['readcount'].rank(ascending=False)
memdf2['write_rank'] = memdf2['writecount'].rank(ascending=False)
memdf2_rw['rw_rank'] = memdf2_rw['count'].rank(ascending=False)
#print(memdf2)
#print(memdf2_rw)

"""memdf2.2"""

total_read = memdf2['readcount'].sum()
total_write = memdf2['writecount'].sum()
total_rw = memdf2_rw['count'].sum()
#print(total_read, total_write, total_rw)

# percentage
memdf2['readpcnt'] = (memdf2['readcount'] / total_read)
memdf2['writepcnt'] = (memdf2['writecount'] / total_write)
memdf2_rw['rwpcnt'] = (memdf2_rw['count'] / total_rw)

# ranking in percentile form
memdf2['read_rank_pcnt'] = memdf2['readpcnt'].rank(ascending=False, pct=True)
memdf2['write_rank_pcnt'] = memdf2['writepcnt'].rank(ascending=False, pct=True)
memdf2_rw['rw_rank_pcnt'] = memdf2_rw['rwpcnt'].rank(ascending=False, pct=True)
#print(memdf2)
#print(memdf2_rw)
save_csv(memdf2, args.output, 0)
save_csv(memdf2_rw, args.output[:-4]+'_rw.csv', 0)

"""memdf2.1 graph"""

fig, ax = plt.subplots(2, figsize=(11,10), constrained_layout=True, sharex=True, sharey=True) # sharex=True: share x axis

#read
x1 = memdf2['read_rank']
y1 = memdf2['readcount']
#write
x2 = memdf2['write_rank']
y2 = memdf2['writecount']
#read+write
x3 = memdf2_rw['rw_rank']
y3 = memdf2_rw['count']

# read/write graph
ax[0].scatter(x1, y1, color='blue', label='read', s=5)
ax[0].scatter(x2, y2, color='red', label='write', s=5)
#ax[0].set_xscale('log')
#ax[0].set_yscale('log')

# legend
ax[0].set_xlabel('ranking')
ax[0].set_ylabel('block access count')
ax[0].legend(loc=(1.0,0.8), ncol=1) #loc = 'best', 'upper right'

# read+write graph
ax[1].scatter(x3, y3, color='green', label='read&write', s=5)
#ax[1].set_ylim([0.5,1e5])
ax[1].set_xscale('log')
ax[1].set_yscale('log')
# legend
ax[1].set_xlabel('ranking')
ax[1].set_ylabel('block access count')
ax[1].legend(loc=(1.0,0.8), ncol=1) #loc = 'best'

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)


"""memdf2.2 graph"""

fig, ax = plt.subplots(2, figsize=(11,10), constrained_layout=True, sharex=True, sharey=True) # sharex=True: share x axis

#read
x1 = memdf2['read_rank_pcnt']
y1 = memdf2['readpcnt']
#write
x2 = memdf2['write_rank_pcnt']
y2 = memdf2['writepcnt']
#read+write
x3 = memdf2_rw['rw_rank_pcnt']
y3 = memdf2_rw['rwpcnt']

#scatter
ax[0].scatter(x1, y1, color='blue', label='read', s=5)
ax[0].scatter(x2, y2, color='red', label='write', s=5)
ax[1].scatter(x3, y3, color='green', label='read+write', s=5)

# legend
ax[0].set_xlabel('ranking (in % form)')
ax[0].set_ylabel('% of reference count')
ax[0].legend(loc='upper right', ncol=1)
#ax[0].set_xlim([-0.1,1])
#ax[0].set_ylim([-0.1,1])

#plt.show()
plt.savefig(args.output[:-4]+'-2.png', dpi=300)
