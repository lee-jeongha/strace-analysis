import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

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

def address_ref(inputdf, concat=False):
    if (concat):
        df = inputdf.groupby(by=['blocknum', 'operation'], as_index=False).sum()
    else:
        df = inputdf.groupby(['blocknum', 'operation'])['blocknum'].count().reset_index(name='count')  # 'blockaddress'와 'type'을 기준으로 묶어서 세고, 이 이름은 'count'로

    return df


## 1. use list of chunk
blkdf = pd.read_csv(args.input, sep=',', chunksize=1000000, header=0, index_col=0, on_bad_lines='skip')
blkdf = list(blkdf)
#---
df1 = pd.DataFrame()
df1_rw = pd.DataFrame()
for i in range(len(blkdf)):
    df = address_ref(blkdf[i], concat=False)
    df1 = pd.concat([df1, df])

#group by type(read or write)
df1 = address_ref(df1, concat=True)

#both read and write
df1_rw = df1.groupby(by=['blocknum'], as_index=False).sum()
df1_rw['operation'] = 'read&write'

df1 = pd.concat([df1, df1_rw], sort=True)
save_csv(df1, args.output, 0)

'''
**blkdf1 graph**
> Specify the axis range (manual margin adjustment required)
'''

blkdf1 = pd.read_csv(args.output, sep=',', header=0, index_col=0, on_bad_lines='skip')

plt.rc('font', size=13)
fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.set_axisbelow(True)
ax.grid(axis='y', color='black', alpha=0.5, linestyle='--')
if args.title != '':
    plt.title(args.title, fontsize=20)

# scatter
x1 = blkdf1['blocknum'][(blkdf1['operation'] == 'read')]
x2 = blkdf1['blocknum'][(blkdf1['operation'] == 'write')]
y1 = blkdf1['count'][(blkdf1['operation'] == 'read')]
y2 = blkdf1['count'][(blkdf1['operation'] == 'write')]
print(x1.max(), x2.max())
print(y1.min(), y1.max())
print(y2.min(), y2.max())

plt.bar(x1, y1, color='blue', label='read')
plt.bar(x2, y2, color='red', label='write')

# legend
fig.supxlabel('unique block number', fontsize=17)
fig.supylabel('access count', fontsize=17)
ax.legend(loc='upper right', ncol=1, fontsize=13)  # loc = 'best'

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)
