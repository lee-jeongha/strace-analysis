import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# add parser
parser = argparse.ArgumentParser(description="plot reference count per each block")

parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt', help='output file')
args = parser.parse_args()

def save_csv(df, filename="output.csv", index=0):
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

'''
##**blkdf1 = access count**
* x axis : unique block number
* y axis : access count per each block
'''

def address_ref(inputdf, concat=False):
  if (concat) :
    df = inputdf.groupby(by=['blocknum', 'operation'], as_index=False).sum()
  else :
    df = inputdf.groupby(['blocknum', 'operation'])['blocknum'].count().reset_index(name='count') # 'blockaddress'와 'type'을 기준으로 묶어서 세고, 이 이름은 'count'로

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

df1 = address_ref(df1, concat=True)

#only read
df1['readcount'] = df1['count']
df1.loc[(df1.operation=='write'), 'readcount'] = np.NaN
#only write
df1['writecount'] = df1['count']
df1.loc[(df1.operation!='write'), 'writecount'] = np.NaN
#read and write
df1_rw = df1.groupby(by=['blocknum'], as_index=False).sum()

save_csv(df1, args.output, 0)
save_csv(df1_rw, args.output[:-4]+'_rw.csv', 0)

'''
**blkdf1 graph**
> Specify the axis range (manual margin adjustment required)
'''

blkdf1 = pd.read_csv(args.output, sep=',', header=0, index_col=0, on_bad_lines='skip')
blkdf1_rw = pd.read_csv(args.output[:-4]+'_rw.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')

#plt.style.use('default')
plt.rcParams['figure.figsize'] = (24, 20)
#plt.rcParams['font.size'] = 12

# scatter
x = blkdf1['blocknum']
y1 = blkdf1['readcount']
y2 = blkdf1['writecount']
print(x.min(), x.max())
print(y1.max(), y2.max())

plt.scatter(x, y1, color='blue', label='read') #aquamarine, s=5
plt.scatter(x, y2, color='red', label='write') #salmon, s=5

# legend
plt.xlabel('unique block number')
plt.ylabel('access count per each block')
plt.legend(loc='upper right', ncol=1) #loc = 'best'
#plt.margins(x=5)

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)
