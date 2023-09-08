from fileio.test.filetrace_test import *

def scenario1():
    inode_table['1'] = ['file1', 0];  inode_table['2'] = ['file2', 0]
    #inode_table = {'file1':1, 'file2':2}

    # [open]
    insert_fdTable(pid=1, fd=3, filename='file1', inode=1)
    insert_fdTable(pid=1, fd=4, filename='file2', inode=2)

    # [dup] fd:3 -> fd:5...?
    copy_fd(pid=1, oldfd=3, newfd=5)

    # [read/pread]
    read_access(pid=1, fd=3, length=3, flag=None, offset=None)
    read_access(pid=1, fd=5, length=7, flag=None, offset=None)
    read_access(pid=1, fd=3, length=3, flag=None, offset=5)
    read_access(pid=1, fd=4, length=8, flag=None, offset=None) # filename이랑 inode 틀려도 fd에 맞게 동작

    print_all_table()

def scenario2():
    inode_table['1'] = ['file1', 0];  inode_table['2'] = ['file2', 0]
    #inode_table = {'file1':1, 'file2':2}

    # [open]
    insert_fdTable(pid=1, fd=3, filename='file1', inode=1)
    insert_fdTable(pid=1, fd=4, filename='file2', inode=2, flag='O_APPEND')

    # [dup] fd:3 -> fd:5...?
    copy_fd(pid=1, oldfd=3, newfd=5)

    # [read/pread, write/pwrite]
    read_access(pid=1, fd=3, length=3, flag=None, offset=None)
    read_access(pid=1, fd=5, length=7, flag=None, offset=None)
    read_access(pid=1, fd=3, length=3, flag=None, offset=5)
    write_access(pid=1, fd=4, length=4, flag=None, offset=None)
    write_access(pid=1, fd=4, length=4, flag=None, offset=None)
    read_access(pid=1, fd=5, length=2, flag=None, offset=None)
    write_access(pid=1, fd=4, length=2, flag=None, offset=3)

    print_all_table()

def scenario3():
    inode_table['1'] = ['file1', 0];  inode_table['2'] = ['file2', 0]
    #inode_table = {'file1':1, 'file2':2}

    # [open]
    insert_fdTable(pid=1, fd=3, inode=1)
    insert_fdTable(pid=1, fd=4, inode=2)#, flag='O_APPEND')

    # [dup] fd:3 -> fd:5...?
    copy_fd(pid=1, oldfd=3, newfd=5)

    # [read/pread]
    read_access(pid=1, fd=3, length=3, flag=None, offset=None)
    read_access(pid=1, fd=5, length=7, flag=None, offset=None)
    read_access(pid=1, fd=3, length=3, flag=None, offset=5)
    read_access(pid=1, fd=4, length=8, flag=None, offset=None)

    # [fork]
    copy_fdTable(1, 2)

    # [read/pread, write/pwrite]
    write_access(pid=1, fd=4, length=4, flag=None, offset=None)
    write_access(pid=1, fd=4, length=4, flag=None, offset=2)#offset=None)
    read_access(pid=2, fd=5, length=2, flag=None, offset=None)
    write_access(pid=2, fd=4, length=2, flag=None, offset=3)

    print_all_table()

def scenario4():
    inode_table['1'] = ['file1', 0];  inode_table['2'] = ['file2', 0]
    #inode_table = {'file1':1, 'file2':2}

    # [open]
    insert_fdTable(pid=1, fd=3, inode=1)
    insert_fdTable(pid=1, fd=4, inode=2)#, flag='O_APPEND')

    # [dup] fd:3 -> fd:5...?
    copy_fd(pid=1, oldfd=3, newfd=5)

    # [read/pread]
    read_access(pid=1, fd=3, length=3, flag=None, offset=None)
    read_access(pid=1, fd=5, length=7, flag=None, offset=None)
    read_access(pid=1, fd=3, length=3, flag=None, offset=5)
    read_access(pid=1, fd=4, length=8, flag=None, offset=None)

    # [clone]
    copy_fdTable(1, 2)

    # [read/pread, write/pwrite]
    write_access(pid=1, fd=4, length=4, flag=None, offset=None)
    write_access(pid=1, fd=4, length=4, flag=None, offset=2)#offset=None)
    read_access(pid=2, fd=5, length=2, flag=None, offset=None)
    write_access(pid=2, fd=4, length=2, flag=None, offset=3)

    print_all_table()

def scenario5():
    inode_table['1'] = ['file1', 0];  inode_table['2'] = ['file2', 0]
    #inode_table = {'file1':1, 'file2':2}

    # [open]
    insert_fdTable(pid=1, fd=3, inode=1)
    insert_fdTable(pid=1, fd=4, inode=2)#, flag='O_APPEND')

    # [dup] fd:3 -> fd:5...?
    copy_fd(pid=1, oldfd=3, newfd=5)

    # [read/pread]
    read_access(pid=1, fd=3, length=3, flag=None, offset=None)
    read_access(pid=1, fd=5, length=7, flag=None, offset=None)
    read_access(pid=1, fd=3, length=3, flag=None, offset=5)
    read_access(pid=1, fd=4, length=8, flag=None, offset=None)

    # [clone] CLONE_FILES
    share_fdTable(1, 2)

    # [read/pread, write/pwrite]
    write_access(pid=1, fd=4, length=4, flag=None, offset=None)
    write_access(pid=1, fd=4, length=4, flag=None, offset=2)#offset=None)
    read_access(pid=2, fd=5, length=2, flag=None, offset=None)
    write_access(pid=2, fd=4, length=2, flag=None, offset=3)

    ##test : file closed from pid2
    remove_fdTable(pid=2, fd=3)

    print_all_table()

def check_brackets_pair(line, start_symbol, end_symbol, offset_idx = 0):
    start_idx = line[offset_idx:].find(start_symbol) + offset_idx
    balanced = 1

    for i in range(start_idx+1, len(line)):
        if line[i] == start_symbol:
            balanced += 1
        elif line[i] == end_symbol:
            balanced -= 1
        
        if balanced == 0:
            end_idx = i
            break

    return start_idx, end_idx

# separate the syscall command and its parameters by spaces
def remove_parenthesis(line, start_symbol, end_symbol):
    start_idx, end_idx = check_brackets_pair(line=line, start_symbol=start_symbol, end_symbol=end_symbol)
    
    line = list(line)
    line[start_idx] = " ";  line[end_idx] = ""
    line = ''.join(line)

    print(line)
    return line

def get_struct(line):
    start_struct_idx = line.find('{st_')
    start_symbol, end_symbol = '{', '}'
    start_idx, end_idx = check_brackets_pair(line=line, start_symbol=start_symbol, end_symbol=end_symbol, offset_idx=start_struct_idx)

    struct = line[start_idx+1:end_idx]
    line = line[:start_idx]+"{struct}"+line[end_idx+1:]

    struct = struct.split('st_')[1:]
    struct = [struct[i].strip(', ') for i in range(len(struct))]
    struct = [struct[i][struct[i].find('=')+1:] for i in range(len(struct))]

    print(line, struct, sep='|||')
    return line, struct

if __name__ == "__main__":
    #scenario1()
    #scenario2()
    scenario3()
    #scenario4()
    #scenario5()

    line1 = "25895 18:49:34.218726 pread64(3</usr/lib/x86_64-linux-gnu/libc-2.31.so>, ""..., 68, 880) = 68"
    output_line = remove_parenthesis(line1, start_symbol='(', end_symbol=')')

    line2 = "25895 18:49:34.218476 fstat(3</etc/ld.so.cache>, {st_dev=makedev(0x8, 0x2), st_ino=8651229, st_mode=S_IFREG|0644, st_nlink=1, st_uid=0, st_gid=0, st_blksize=4096, st_blocks=264, st_size=134205, st_atime=1662003001 /* 2022-09-01T12:30:01.452429312+0900 */, st_atime_nsec=452429312, st_mtime=1661289386 /* 2022-08-24T06:16:26.352487490+0900 */, st_mtime_nsec=352487490, st_ctime=1661289386 /* 2022-08-24T06:16:26.356487452+0900 */, st_ctime_nsec=356487452}) = 0"
    output_line, struct = get_struct(line2)
    inode = struct[1];  size = struct[8]
    print(struct, inode, size, sep='\n')