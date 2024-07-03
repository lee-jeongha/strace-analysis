def simulation(df, block_rank, readcnt, writecnt):
    for index, row in df.iterrows():  ### one by one
        ### Increase readcnt/writecnt by matching 'operation' and block_rank
        acc_rank = block_rank.reference(row['blocknum'])
        if acc_rank == -1:
            continue
        else:
            if (row['operation'] == 'read'):  ### if the 'operation' is 'read'
                try:
                    readcnt[acc_rank] += 1  # Increase [acc_rank]th element of readcnt by 1
                except IndexError:  # ***list index out of range
                    for i in range(len(readcnt), acc_rank + 1):
                        readcnt.insert(i, 0)
                    readcnt[acc_rank] += 1

            else:   ### if the 'operation' is 'write'
                try:
                    writecnt[acc_rank] += 1 # Increase [acc_rank]th element of writecnt by 1
                except IndexError:
                    for i in range(len(writecnt), acc_rank + 1):
                        writecnt.insert(i, 0)
                    writecnt[acc_rank] += 1

    return block_rank, readcnt, writecnt

#----------------------
def overall_rank_simulation(df, block_rank, read_cnt, write_cnt):
    for index, row in df.iterrows():  ### one by one
        ### Increase read_cnt/write_cnt by matching 'operation' and block_rank
        acc_rank = block_rank.reference(row['blocknum'])
        if acc_rank == -1:
            continue
        else:
            if (row['operation'] == 'read'):  ### if the 'operation' is 'read'
                try:
                    read_cnt[acc_rank] += 1  # Increase [acc_rank]th element of read_cnt by 1
                except IndexError:  # ***list index out of range
                    for i in range(len(read_cnt), acc_rank + 1):
                        read_cnt.insert(i, 0)
                    read_cnt[acc_rank] += 1

            else:   ### if the 'operation' is 'write'
                try:
                    write_cnt[acc_rank] += 1 # Increase [acc_rank]th element of write_cnt by 1
                except IndexError:
                    for i in range(len(write_cnt), acc_rank + 1):
                        write_cnt.insert(i, 0)
                    write_cnt[acc_rank] += 1

    return block_rank, read_cnt, write_cnt

def separately_rank_simulation(df, read_block_rank, read_cnt, write_block_rank, write_cnt):
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
