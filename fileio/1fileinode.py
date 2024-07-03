import argparse
import pandas as pd
import csv
import itertools
import string
import random
import math

#----
def random_inode_list(length, num_of_inode):
    #string_pool = string.hexdigits  # 0~9, a~f, A~F
    string_pool = string.ascii_lowercase
    digit_pool = string.digits

    random_digit = list(itertools.combinations_with_replacement(digit_pool, length-2))

    inode_list = []
    for i in range(num_of_inode):
        result = random.choice(string_pool)
        digit_result = random.choice(random_digit)
        result += ''.join(digit_result)  # get random digit
        result += random.choice(string_pool)

        inode_list.append(result)
        random_digit.remove(digit_result)

    return inode_list

#----
# check duplicate
def drop_duplicate_inode(df):
    df['dup'] = df.duplicated(['inode'], keep=False)

    for index, rows in df.iterrows():
        if (rows['dup']) and (rows['filename'] in file_link.keys()):
            df = df.drop([index])
    df.loc[:,'dup'] = df.duplicated(['inode'], keep=False)

    dup_cnt = len(df[df['dup']])  #len(df) - len(df['inode'].value_counts())
    random_length = math.ceil(math.log(dup_cnt, 26)) if dup_cnt > 0 else 0
    random_str = list(itertools.product(string.ascii_lowercase, repeat=random_length))

    for index, rows in df.iterrows():
        if rows['dup']:
            result = random.choice(random_str)
            df.loc[index, 'inode'] = df.loc[index, 'inode']+''.join(result)
            random_str.remove(result)

    df = df.drop(columns=['dup'])
    return df

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')

    args = parser.parse_args()

    # get dataframe
    #df = pd.read_csv(args.input, sep=',', header=None)
    rf = open(args.input, 'rt')
    reader = csv.reader(rf)

    csv_list = []
    for l in reader:
        csv_list.append(l)
    rf.close()
    df = pd.DataFrame(csv_list)

    file_link = dict()

    # get file list
    df = df[[9, 10]]  # column9 : filename, column10 : inode
    df.columns = ['filename', 'inode']
    df = df.dropna(axis=0, subset='filename')
    df = df.drop_duplicates()

    df['filename'] = df['filename'].str.replace("'", "")    #, regex = True)
    df['inode'] = df['inode'].replace('', None)

    for index, rows in df['filename'].iteritems():
        if rows and ('=>' in rows):
            separator = rows.find('=>')
            df.loc[index, 'filename'] = rows[separator+2:]
            file_link[rows[:separator]] = rows[separator+2:]

    df = df[~df['filename'].str.contains('\|\|', na=False, case=False)]

    df = df.sort_values(by='inode', ascending=False)
    df = df.drop_duplicates(subset='filename', keep='first')
    df = df.reset_index(drop=True)

    # fill random inode to null value
    count_non_inode = df['inode'].isnull().sum()
    inode_list = random_inode_list(length=15, num_of_inode=count_non_inode)
    fill = pd.DataFrame(index=df.index[df.isnull().any(axis=1)], data=inode_list, columns=['inode'])
    df = df.fillna(fill)

    df = drop_duplicate_inode(df=df)

    # save file-inode list
    df.to_csv(args.output, header=['filename', 'inode'], index=False)