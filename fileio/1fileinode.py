import argparse
import pandas as pd
import csv
import os
import subprocess   # to get cmd results
import string
import random

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')

args = parser.parse_args()

#----
def random_str(length):
    string_pool = string.digits  # 0~9
    result = ''
    for i in range(length):
        result += random.choice(string_pool)  # get random number
    return result

#----
# get dataframe
#df = pd.read_csv(args.input, sep=',', header=None)
rf = open(args.input, 'rt')
reader = csv.reader(rf)

csv_list = []
for l in reader:
    csv_list.append(l)
rf.close()
df = pd.DataFrame(csv_list)

for index, rows in df[8].iteritems():
    if rows and ('->' in rows):
        separator = rows.find('->')
        df.loc[index, 8] = rows[separator+2:]

# get file list
df = df[[8, 9]]  # column8 : filename, column9 : inode
df = df.dropna(axis=0, subset=8)
df = df.drop_duplicates()

df = df[~df[8].str.contains('pipe', na=False, case=False)]
df = df[~df[8].str.contains('socket', na=False, case=False)]
df = df[~df[8].str.contains('::', na=False, case=False)]

df = df.sort_values(by=9, ascending=False)
df = df.drop_duplicates(subset=8, keep='first')

for index, rows in df[9].iteritems():
    if not rows:
        df.loc[index, 9] = random_str(12)

# save file-inode list
df.to_csv(args.output, header=['filename', 'inode'], index=False)
