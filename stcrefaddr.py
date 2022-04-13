import argparse
import pandas as pd

# add parser
parser = argparse.ArgumentParser(description="refine for read,write,lseek,pread64,pwrite64")
parser.add_argument('input', metaver='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument('output', metaver='O', type=str, nargs='?', default='output.txt', help='output file')
args = parser.parse_args()

# read logfile
stcparse = pd.read_csv(args.input, header=None)
stcparse

# remove [open, close, creat, openat] rows 
stcparse = stcparse[(stcparse[0] != 2) & (stcparse[0] != 3) & (stcparse[0] != 85) & (stcparse[0] != 257)]
stcparse = stcparse.drop(6, axis=1)

# lseek이 위치한 행 확인하기
'''lseek = stcparse.index[stcparse[0]==8].tolist()
lseek'''

# add base address with offset
stcparse[3] = stcparse[3].fillna('0x0')
stcparse[2] = [int(i,16) for i in stcparse[2]]
stcparse[3] = [int(i,16) for i in stcparse[3]]
stcparse[2] = stcparse[2] + stcparse[3]
# drop offset column
stcparse = stcparse.drop(3, axis=1)

# remain only actual read and write
stcparse = stcparse.drop(4, axis=1)
rw0 = stcparse.index[stcparse[5]==0].tolist() # unsuccessful read, write
stcparse = stcparse.drop(rw0, axis=0)

# calculate end address
stcparse[5] = stcparse[2] + stcparse[5].astype('int')

# block size=4KB
stcparse[2] = (stcparse[2].apply(lambda x: x >> 12))
stcparse[5] = (stcparse[5].apply(lambda x: x >> 12))

stcparse.to_csv(args.output)
