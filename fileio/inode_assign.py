import pandas as pd
import csv
import itertools
import string
import random
import math

def convert_to_int_str(val):
    if pd.isna(val):  # Note: `NaN` is of `float` type, so we must check for it before converting to int.
        return val
    elif isinstance(val, (int, float)):
        return str(int(val))
    else:  # if already `str` type
        return val

#----
def random_inode_list(length, num_of_inode, numeric_only=False):
    if numeric_only:
        string_pool = string.digits
    else:
        #string_pool = string.hexdigits  # 0~9, a~f, A~F
        string_pool = string.ascii_lowercase

    digit_pool = string.digits

    random_digit = list(itertools.combinations_with_replacement(digit_pool, length-2))

    inode_list = []
    for i in range(num_of_inode):
        result = random.choice(string_pool.strip('0')) # No zeros for the first digit
        digit_result = random.choice(random_digit)
        result += ''.join(digit_result)  # get random digit
        result += random.choice(string_pool)

        inode_list.append(result)
        random_digit.remove(digit_result)

    return inode_list

#----
# check duplicate
def drop_duplicate_inode(df, file_link, numeric_only=False):
    df['dup'] = df.duplicated(['inode'], keep=False)

    # Drop rows with duplicated inodes whose filenames are in file_link
    mask = df['dup'] & df['filename'].isin(file_link.keys())
    df = df[~mask].copy()
    # Update duplication status after filtering
    df['dup'] = df.duplicated(['inode'], keep=False)

    dup_cnt = len(df[df['dup']])  #len(df) - len(df['inode'].value_counts())
    if numeric_only:
        random_length = math.ceil(math.log(dup_cnt, 10)) if dup_cnt > 0 else 0
        random_str = list(itertools.product(string.digits, repeat=random_length))
    else:
        random_length = math.ceil(math.log(dup_cnt, 26)) if dup_cnt > 0 else 0
        random_str = list(itertools.product(string.ascii_lowercase, repeat=random_length))

    for index, rows in df.iterrows():
        if rows['dup']:
            result = random.choice(random_str)
            df.loc[index, 'inode'] = str(df.loc[index, 'inode'])+''.join(result)
            random_str.remove(result)

    df = df.drop(columns=['dup'])
    return df

#----
def organize_file_inodes(input_dataframe, numeric_only=False):
    df = input_dataframe
    file_link = dict()
    same_inode_list = []

    # column4 : fd, column9 : filename, column10 : inode
    df = df[
        ~(df[4].astype(str).str.contains('\|\|', na=False) & df[9].str.contains('\|\|', na=False)) |
        ~df[9].str.contains('pipe', na=False) |
        ~df[9].str.contains('socket', na=False)
    ]

    # get file list
    df = df[[9, 10]]  # column9 : filename, column10 : inode
    df.columns = ['filename', 'inode']
    df = df.dropna(axis=0, subset='filename')
    df = df.drop_duplicates()

    df['filename'] = df['filename'].str.replace("'", "")    #, regex = True)
    df['inode'] = df['inode'].replace('', None)
    df['inode'] = df['inode'].apply(convert_to_int_str)

    # Case 1: Same file with different filenames
    for index, rows in df['filename'].items():
        if rows and ('=>' in rows):
            separator = rows.find('=>')
            df.loc[index, 'filename'] = rows[separator+2:]
            file_link[rows[:separator]] = rows[separator+2:]

    df = df.sort_values(by='inode', ascending=False)
    df = df.drop_duplicates(subset='filename', keep='first')
    df = df.reset_index(drop=True)

    # fill random inode to null value
    count_non_inode = df['inode'].isnull().sum()
    inode_list = random_inode_list(length=9, num_of_inode=count_non_inode, numeric_only=numeric_only)
    fill = pd.DataFrame(index=df.index[df.isnull().any(axis=1)], data=inode_list, columns=['inode'])
    df = df.fillna(fill)

    # Case 2: Different files share the same inode number
    df = drop_duplicate_inode(df=df, file_link=file_link, numeric_only=numeric_only)

    # Case 1
    for k, v in file_link.items():
        inode = df.loc[df['filename'] == v, 'inode'].item()
        same_inode_list.append({'filename':k, 'inode': inode})
    df = pd.concat([df, pd.DataFrame(same_inode_list)], ignore_index=True)

    return df

def save_filename_inode_list(input_filename, output_filename, delimiter=',', numeric_only=False):
    output_df = pd.DataFrame()

    try:
        # get dataframe
        df = pd.read_csv(input_filename+'.csv', sep=delimiter, header=None, names=list(range(11)))
        output_df = organize_file_inodes(df, numeric_only=numeric_only)

    except Exception as e:
        print(e)
        dfs = pd.read_csv(input_filename+'.csv', sep=delimiter, header=None, chunksize=10000, names=list(range(11)), quoting=csv.QUOTE_NONE)
        for df in dfs:
            temp_df = organize_file_inodes(df, numeric_only=numeric_only)
            output_df = pd.concat([output_df, temp_df])
            output_df = output_df.drop_duplicates(subset=['filename'], keep='first')

    # save file-inode list
    output_df.to_csv(output_filename+'.csv', header=['filename', 'inode'], index=False, sep=delimiter)

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file path')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file path')

    args = parser.parse_args()

    save_filename_inode_list(args.input, args.output, numeric_only=True)
