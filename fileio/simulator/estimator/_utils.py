import pandas as pd
from utils import load_json, save_json

#----------------------
def simulation_by_operation_type(df, read_block_rank, read_cnt, write_block_rank, write_cnt):
    for index, row in df.iterrows():  ### one by one
        ### Increase read_cnt/write_cnt by matching 'operation' and block_rank
        if (row['operation'] == 'read'):  ### if the 'operation' is 'read'
            acc_rank = read_block_rank.reference(row['blocknum'])
            if acc_rank == -1:
                continue
            try:
                read_cnt[acc_rank] += 1  # Increase [acc_rank]th element of read_cnt by 1
            except IndexError:  # ***list index out of range
                for i in range(len(read_cnt), acc_rank + 1):
                    read_cnt.insert(i, 0)
                read_cnt[acc_rank] += 1

        else:   ### if the 'operation' is 'write'
            acc_rank = write_block_rank.reference(row['blocknum'])
            if acc_rank == -1:
                continue
            try:
                write_cnt[acc_rank] += 1 # Increase [acc_rank]th element of write_cnt by 1
            except IndexError:
                for i in range(len(write_cnt), acc_rank + 1):
                    write_cnt.insert(i, 0)
                write_cnt[acc_rank] += 1

    return read_block_rank, read_cnt, write_block_rank, write_cnt

def simulation_regardless_of_type(df, block_rank, ref_cnt):
    for index, row in df.iterrows():  ### one by one
        ### Increase readcnt/writecnt by matching 'type' and block_rank
        acc_rank = block_rank.reference(row['blocknum'])
        if acc_rank == -1:
            continue
        else:
            try:
                ref_cnt[acc_rank] += 1  # Increase [acc_rank]th element of readcnt by 1
            except IndexError:  # ***list index out of range
                for i in range(len(ref_cnt), acc_rank + 1):
                    ref_cnt.insert(i, 0)
                ref_cnt[acc_rank] += 1

    return block_rank, ref_cnt

#----------------------
def mp_estimator_simulation(ref_block, startpoint, endpoint_q, input_filename, output_filename, operation='all'):
    block_rank = list()
    ref_cnt = list()
    
    if (startpoint > 0):
        filename = output_filename + "-" + operation + "_checkpoint" + str(startpoint - 1) + ".json"
        saving_list = ['block_rank', 'ref_cnt']

        block_rank, ref_cnt = load_json(saving_list, filename)
        ref_block.set(block_rank)
        # print(block_rank, ref_cnt)

    i = startpoint
    while True:
        if not startpoint:
            blkdf = pd.read_csv(input_filename + '.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
        else:
            try:
                blkdf = pd.read_csv(input_filename + '_' + str(i) + '.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')
            except FileNotFoundError:
                print("no file named:", input_filename + '_' + str(i) + '.csv')
                break

        if operation == 'read':
            blkdf = blkdf[blkdf['operation'] == 'read']
        elif operation == 'write':
            blkdf = blkdf[blkdf['operation'] == 'write']
        else:
            #print("choose operation 'read' or 'write'")
            #return
            pass

        ref_block, ref_cnt = simulation_regardless_of_type(blkdf, ref_block, ref_cnt)
        block_rank = ref_block.get()

        if not startpoint:
            filename = output_filename + "-" + operation + ".json"
        else:
            filename = output_filename + "-" + operation + "_checkpoint" + str(i) + ".json"
        savings = {'block_rank': block_rank, 'ref_cnt': ref_cnt}
        save_json(savings, filename)

        if not startpoint:
            break
        else:
            i += 1
    endpoint_q.put(i)    # return i
