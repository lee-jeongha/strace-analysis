import argparse
import pandas as pd

# add parser
parser = argparse.ArgumentParser(description="refine for read,write,lseek,pread64,pwrite64")

parser.add_argument('input', metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument('output', metavar='O', type=str, nargs='?', default='output.txt', help='output file')
args = parser.parse_args()

# read logfile
df = pd.read_csv(args.input, header=None)

#---

# In read/pread4, 0 means end of file.
# In write/pwrite64, 0 means nothing was written.
df = df[df[5]!=0]

# filter error and stdin/out/err
df = df[df[4]!='error'] # error case
df = df[(df[3]!=0) & (df[3]!=1) & (df[3]!=2)] # stdin/stdout/stderr

# add base address with offset
df[4] = [int(i) for i in df[4]]
df[5] = df[4] + df[5]

# drop file-descriptor column
df = df.drop(3, axis=1)

#---

# block size == 512Byte
df[4] = [i//512 for i in df[4]]
df[5] = [i//512 for i in df[5]]

# time
df[0] = [(float(i[6:]) + int(i[3:5])*60 + int(i[:2])*60*60) for i in df[0]]
df[0] = [(i - df[0][0]) for i in df[0]]

#---

# make block_number of each file blocks
blocks = dict()
blocknum = 0
for index, data in df.iterrows():
    # index: index of each row
    # data: data of each row
    block_range = range(data[4], data[5]+1)

    for i in block_range:
      pair = str(i)+","+str(data[6]) # 'block,inode' pair
      if not pair in blocks:
        blocks[pair] = blocknum
        blocknum += 1

#---

# set block_number
filerw = list()
for index, data in df.iterrows():
  if data[4]==data[5]:
    pair = str(data[4])+","+str(data[6]) # 'block,inode' pair
    blocknum = blocks.get(pair)
    filerw.append([data[0], data[1], data[2], str(blocknum)])
    continue
  block_range = range(data[4], data[5]+1)
  for i in block_range:
    pair = str(i)+","+str(data[6]) # 'block,inode' pair
    blocknum = blocks.get(pair)
    filerw.append([data[0], data[1], data[2], str(blocknum)])

#---

df2 = pd.DataFrame(filerw, columns=["T", "pid", "operation", "blocknum"])
df2.to_csv(args.output)
