import argparse
import pandas as pd
import numpy as np

# add parser
parser = argparse.ArgumentParser(description="refine for read,write,lseek,pread64,pwrite64")

parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt', help='output file')
args = parser.parse_args()

# column
C_time=0
C_pid=1
C_cpid=2    # child process pid
C_op=3    # operation
C_fd=4
C_offset=5
C_length=6
C_ino=7   # inode


# read logfile
df = pd.read_csv(args.input, header=None)

#---

# In read/pread4, 0 means end of file.
# In write/pwrite64, 0 means nothing was written.
df = df[df[C_length]!=0]

# filter error and stdin/out/err
df = df[df[5]!='error'] # error case
df = df[(df[C_fd]!=0) & (df[C_fd]!=1) & (df[C_fd]!=2)] # stdin/stdout/stderr

# add base address with offset
df[C_offset] = [int(i) for i in df[C_offset]]
df[C_length] = df[C_offset] + df[C_length]

# drop file-descriptor column
df = df.drop(C_fd, axis=1)

#---

# block size == 512Byte
df[C_offset] = [i//512 for i in df[C_offset]]
df[C_length] = [i//512 for i in df[C_length]]

# time
df[C_time] = [(float(i[6:]) + int(i[3:5])*60 + int(i[:2])*60*60) for i in df[C_time]]
start_time = float(df[C_time][0])
df[C_time] = [(float(i) - start_time) for i in df[C_time]]

# operation
df = df.replace('pread64','read')
df = df.replace('pwrite64','write')

#---

# make block_number of each file blocks
blocks = dict()
blocknum = 0
for index, data in df.iterrows():
    # index: index of each row
    # data: data of each row
    block_range = range(data[C_offset], data[C_length]+1)

    for i in block_range:
      pair = str(i)+","+str(data[C_ino]) # 'block,inode' pair
      if not pair in blocks:
        blocks[pair] = blocknum
        blocknum += 1

#---

# set block_number
filerw = list()
for index, data in df.iterrows():
  if data[C_offset]==data[C_length]:
    pair = str(data[C_offset])+","+str(data[C_ino]) # 'block,inode' pair
    blocknum = blocks.get(pair)
    filerw.append([data[C_time], data[C_pid], data[C_op], str(blocknum), data[C_ino]])
    continue
  block_range = range(data[C_offset], data[C_length]+1)
  for i in block_range:
    pair = str(i)+","+str(data[C_ino]) # 'block,inode' pair
    blocknum = blocks.get(pair)
    filerw.append([data[C_time], data[C_pid], data[C_op], str(blocknum), data[C_ino]])

#---

# separate read/write
df2 = pd.DataFrame(filerw, columns=["time", "pid", "operation", "blocknum", "inode"])
df2["read_blk"] = df2["blocknum"]
df2["write_blk"] = df2["blocknum"]
df2.loc[(df2.operation != "read"), "read_blk"] = np.NaN
df2.loc[(df2.operation != "write"), "write_blk"] = np.NaN

df2.to_csv(args.output)