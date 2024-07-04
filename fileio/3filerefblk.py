import argparse
import pandas as pd
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from utils.plot_graph import plot_frame

#---
def filter_trace(input_df, inode_df, blocksize=4096, redundant_file_list=['UNIX:', 'PIPE:', '/dev/shm'], redundant_pid_list=[]):
    # In read/pread4, 0 means end of file.
    # In write/pwrite64, 0 means nothing was written.
    input_df = input_df[input_df[C_length] != 0]

    # filter error and stdin/out/err
    input_df = input_df[input_df[C_offset] != 'error']  # error case
    input_df = input_df[(input_df[C_fd] != 0) & (input_df[C_fd] != 1) & (input_df[C_fd] != 2)]

    df = pd.merge(input_df, inode_df, how='left', on='inode')

    try:
        df = df[~df['filename'].str.contains('|'.join(redundant_file_list), na=False, case=True)]
    except AttributeError as e: # Can only use .str accessor with string values!
        print(e); exit()

    try:
        for p in redundant_pid_list:
            df = df[df[C_pid] != p]
            df = df[df[C_ppid] != p]
    except AttributeError as e:
        print(e); exit()

    # add base address with offset
    df[C_offset] = [int(i) for i in df[C_offset]]
    df[C_length] = [int(i) for i in df[C_length]]
    df[C_length] = df[C_offset] + df[C_length] - 1

    # drop file-descriptor & filename column
    df = df.drop(columns=[C_fd, 'filename'])

    # if block size = 512B, shift = 9
    shift = int(math.log(blocksize, 2))
    df[C_offset] = [i >> shift for i in df[C_offset]]
    df[C_length] = [i >> shift for i in df[C_length]]

    return df

#---

# time
def time_interval(start_timestamp, timestamp):
    start_time = [] # [hour, min, sec, usec]
    start_time.append(int(start_timestamp[:2]))
    start_time.append(int(start_timestamp[3:5]))
    start_time.append(int(start_timestamp[6:8]))
    start_time.append(int(start_timestamp[9:]))

    time = [] # [hour, min, sec, usec]
    time.append(int(timestamp[:2]))
    time.append(int(timestamp[3:5]))
    time.append(int(timestamp[6:8]))
    time.append(int(timestamp[9:]))

    # micro second
    if start_time[3] > time[3]:
        usec = (1000000 + time[3]) - start_time[3]
        time[2] -= 1
    else:
        usec = time[3] - start_time[3]

    # second
    if start_time[2] > time[2]:
        sec = (60 + time[2]) - start_time[2]
        time[1] -= 1
    else:
        sec = time[2] - start_time[2]
    
    # minute
    if start_time[1] > time[1]:
        min = (60 + time[1]) - start_time[1]
        time[0] -= 1
    else:
        min = time[1] - start_time[1]

    # hour
    if start_time[0] > time[0]:
        hour = (24 + time[0]) - start_time[0]
    else:
        hour = time[0] - start_time[0]
    
    #return str(hour*3600 + min*60 + sec) + "." + '{0:>06d}'.format(usec)
    return (hour*3600 + min*60 + sec) + round(usec / 1000000, 6)

#---

# assign block_number to each file blocks (make 'unq_blocks_dict')
def make_unq_block_num(df):
    unq_blocks_dict = dict()
    blocknum = 0
    for index, data in df.iterrows():
        # index: index of each row
        # data: data of each row
        block_range = range(data[C_offset], data[C_length] + 1)

        for i in block_range:
            pair = str(i) + "," + str(data[C_ino])  # 'block,inode' pair
            if not pair in unq_blocks_dict:
                unq_blocks_dict[pair] = blocknum
                blocknum += 1
    return df, unq_blocks_dict

#---

# set block_number to each unique block using 'unq_blocks_dict'
def set_unq_block_num(df, unq_blocks_dict):
    filerw = list()
    for index, data in df.iterrows():
        if data[C_offset] == data[C_length]:
            pair = str(data[C_offset]) + "," + str(data[C_ino])  # 'block,inode' pair
            blocknum = unq_blocks_dict.get(pair)
            filerw.append([data[C_time], data['time_interval'], data[C_pid], data[C_op], str(blocknum), data[C_ino], data[C_offset]])
            continue
        block_range = range(data[C_offset], data[C_length] + 1)
        for i in block_range:
            pair = str(i) + "," + str(data[C_ino])  # 'block,inode' pair
            blocknum = unq_blocks_dict.get(pair)
            filerw.append([data[C_time], data['time_interval'], data[C_pid], data[C_op], str(blocknum), data[C_ino], i])
    return filerw

#---

# plot graph
def plot_ref_addr_graph(blkdf, fig_title, filename):
    '''real_time'''
    fig, ax = plot_frame((1, 1), (8, 8), title=fig_title, xlabel='Time(sec)', ylabel='Unique block number', log_scale=False)
    ax.xaxis.set_major_locator(MaxNLocator(7))

    # scatter
    x1 = blkdf['time_interval'][(blkdf['operation']=='read')]
    x2 = blkdf['time_interval'][(blkdf['operation']=='write')]
    y1 = blkdf.loc[(blkdf['operation']=='read'), ['blocknum']]
    y2 = blkdf.loc[(blkdf['operation']=='write'), ['blocknum']]

    ax.scatter(x1, y1, color='blue', label='read', s=1)
    ax.scatter(x2, y2, color='red', label='write', s=1)

    # legend
    ax.legend(loc=(0.2, 1.01), ncol=2, fontsize=20, markerscale=10)  # loc='upper left'

    #plt.show()
    plt.savefig(filename+'_realtime.png', dpi=300)

    #-----
    '''logical_time_single'''
    fig, ax = plot_frame((1, 1), (8, 8), title=fig_title, xlabel='Logical time', ylabel='Unique block number', log_scale=False)
    ax.xaxis.set_major_locator(MaxNLocator(7))

    # scatter
    x1 = blkdf.index[(blkdf['operation']=='read')]
    x2 = blkdf.index[(blkdf['operation']=='write')]
    ax.scatter(x1, y1, color='blue', label='read', s=1)
    ax.scatter(x2, y2, color='red', label='write', s=1)

    # legend
    ax.legend(loc=(0.2, 1.01), ncol=2, fontsize=20, markerscale=10)  # loc='upper left'

    #plt.show()
    plt.savefig(filename+'_logicaltime.png', dpi=300)

#---

if __name__=="__main__":
    # add parser
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')
    parser.add_argument("--filename_inode", "-f", metavar='Fi', type=str,
                        nargs='?', default='file-inode.txt', help='filename-inode file')
    parser.add_argument("--title", "-t", metavar='T', type=str,
                        nargs='?', default='', help='title of a graph')
    parser.add_argument("--blocksize", "-b", metavar='B', type=int,
                        nargs='?', default=4096, help='block size')
    args = parser.parse_args()

    # column
    C_time = 'time' # 0
    C_pid = 'pid'   # 1
    C_ppid = 'ppid'  # 2
    C_op = 'operation'  # 3
    C_fd = 'fd' # 4
    C_offset = 'offset' # 5
    C_length = 'length' # 6
    C_ino = 'inode'   # 7

    # read logfile
    input_df = pd.read_csv(args.input+'.csv', header=None, names=[C_time, C_pid, C_ppid, C_op, C_fd, C_offset, C_length, C_ino], on_bad_lines='warn')
    inode_df = pd.read_csv(args.filename_inode+'.csv', header=0, on_bad_lines='warn')

    redundant_file_list = ['UNIX:', 'PIPE:', 'pipe:', '/dev/shm/', 'anon_inode:', '/proc/', '/sys/devices/', '/dev/mali', 'TCP:\[', 'TCPv6:\[', 'UDP:\[']
    redundant_pid_list = []

    df = filter_trace(input_df=input_df, inode_df=inode_df, blocksize=args.blocksize,
                      redundant_file_list=redundant_file_list, redundant_pid_list=redundant_pid_list)

    time_col = df[C_time].to_list()
    start_timestamp = time_col[0]
    time_col = [time_interval(start_timestamp, i) for i in time_col]
    df.insert(1, 'time_interval', time_col)
    pd.options.display.float_format = '{:.6f}'.format
    df = df.sort_values(by='time_interval')

    # operation
    df = df.replace('pread64', 'read')
    df = df.replace('pwrite64', 'write')

    df, unq_blocks_dict = make_unq_block_num(df=df)
    filerw = set_unq_block_num(df=df, unq_blocks_dict=unq_blocks_dict)

    # separate read/write
    blkdf = pd.DataFrame(filerw, columns=["time", "time_interval", "pid", "operation", "blocknum", "inode", "blk_offset"])
    blkdf.to_csv(args.output+'.csv', index=False)

    # plot graph
    blkdf['blocknum'] = pd.to_numeric(blkdf['blocknum'])
    plot_ref_addr_graph(blkdf=blkdf, fig_title=args.title, filename=args.output)