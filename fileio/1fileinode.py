import argparse
import pandas as pd
import csv
import itertools
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
    string_pool = string.hexdigits  # 0~9, a~f, A~F
    result = ''
    for i in range(length):
        result += random.choice(string_pool)  # get random string
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

for index, rows in df[9].iteritems():
    if rows and ('=>' in rows):
        separator = rows.find('=>')
        df.loc[index, 9] = rows[separator+2:]

# get file list
df = df[[9, 10]]  # column9 : filename, column10 : inode
df = df.dropna(axis=0, subset=9)
df = df.drop_duplicates()

df[9] = df[9].str.replace('`', '')#, regex = True)
df[10] = df[10].replace('', None)

df = df[~df[9].str.contains('pipe:\[', na=False, case=False)]
df = df[~df[9].str.contains('socket:\[', na=False, case=False)]
df = df[~df[9].str.contains('\|\|', na=False, case=False)]

df = df.sort_values(by=10, ascending=False)
df = df.drop_duplicates(subset=9, keep='first')
df = df.reset_index(drop=True)

for index, rows in df[10].iteritems():
    if not rows:
        df.loc[index, 10] = random_str(15)

# save file-inode list
df.to_csv(args.output, header=['filename', 'inode'], index=False)
