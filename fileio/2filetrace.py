import argparse
import pandas as pd
import copy
import random
import string

### 1. get filename-inode pair
inode_table = dict()    # {'inode': [filename, file_size]}  ### 원래는 {'inode': [filename, ref_count]}

### 2. object for manage opened files
class openFileTable:
    def __init__(self):
        self.file_info = dict()    # {'oftid': [inode, ref_count, flag, offset]}
        self.oftid_cnt = 0

    def insert_oft_fio(self, inode, flag, offset):    # syscall 'open()'
        self.oftid_cnt += 1
        self.file_info[self.oftid_cnt] = [inode, 1, flag, offset]
        return self.oftid_cnt

    def set_oft_fio_offset(self, oftid, offset):
        self.file_info[oftid][3] = offset
        return self.file_info[oftid]

    def set_oft_fio_flag(self, oftid, flag):
        self.file_info[oftid][2] = flag
        return self.file_info[oftid]

    def get_oft_fio(self, oftid):
        return self.file_info[oftid]

    def increase_oft_fio_ref_count(self, oftid):    # syscall 'clone()', 'fork()'
        self.file_info[oftid][1] += 1
        return self.file_info[oftid]

    def reduce_oft_fio_ref_count(self, oftid):    # syscall 'close()'
        self.file_info[oftid][1] -= 1
        if self.file_info[oftid][1] == 0:
            self.remove_oft_fio(oftid)
            return 0
        else:
            return self.file_info[oftid]

    def remove_oft_fio(self, oftid):    # when no process is referencing this file
        oft_file_info = self.file_info[oftid]
        self.file_info.pop(oftid)
        return oft_file_info

open_file_table = openFileTable()

### 3. objects for trace read/write operations
class fdTable:    # File descriptor table of process
    def __init__(self, pid, ppid=None):
        self.pid = pid
        self.ppid = ppid
        self.fd_oft = dict()    # {'fd': oftid}

    def set_fd_oft(self, fd, oftid):    # syscall 'open()'
        self.fd_oft[fd] = oftid

    def get_fd_oft(self, fd):
        return self.fd_oft[fd]

    def remove_fd_oft(self, fd):    # syscall 'close()'
        fd_oftid = self.fd_oft[fd]
        self.fd_oft.pop(fd)
        return fd_oftid
    
    def copy(self):
        return copy.deepcopy(self)    # fdTable(self.pid.copy(), self.fd_oft.copy())

process_dict = dict()    # {'pid': fdTable}

#-----
# open new file in a process
def insert_fdTable(pid, fd, inode, flag=None, offset=None):
    if not offset:
        offset = 0
    if not flag:
        flag = ''

    try:
        pid_fd_table = process_dict[pid]
    except:
        pid_fd_table = fdTable(pid)
        process_dict[pid] = pid_fd_table
    oftid = open_file_table.insert_oft_fio(inode=str(inode), flag=flag, offset=offset)
    pid_fd_table.set_fd_oft(fd, oftid)

# close a file in a process
def remove_fdTable(pid, fd):
    try:
        pid_fd_table = process_dict[pid]
        oftid = pid_fd_table.remove_fd_oft(fd)
        file_info = open_file_table.reduce_oft_fio_ref_count(oftid=oftid)
    except KeyError:
        raise KeyError

# inherits a copy of file descriptor table (syscall 'fork()', 'clone()')
def copy_fdTable(ppid, cpid):
    ppid_fd_table = process_dict[ppid]
    cpid_fd_table = ppid_fd_table.copy()
    cpid_fd_table.pid = cpid
    cpid_fd_table.ppid = ppid

    for k, v in cpid_fd_table.fd_oft.items():
        open_file_table.file_info[v][1] += 1

    process_dict[cpid] = cpid_fd_table

# share same file descriptor table ('CLONE_FILES' flag)
def share_fdTable(ppid, cpid):
    ppid_fd_table = process_dict[ppid]
    cpid_fd_table = ppid_fd_table

    process_dict[cpid] = cpid_fd_table

# copy file descriptor (syscall 'dup()')
def copy_fd(pid, oldfd, newfd):
    pid_fd_table = process_dict[pid]
    oftid = pid_fd_table.fd_oft[oldfd]
    pid_fd_table.fd_oft[newfd] = oftid    # copy oftid
    open_file_table.file_info[oftid][1] += 1

# read file
def read_access(pid, fd, length, flag, offset=None, filename=None):
    pid_fd_table = process_dict[pid]
    oftid = pid_fd_table.fd_oft[fd]
    file_info = open_file_table.get_oft_fio(oftid)    # [inode, ref_count, flag, offset]

    if pid_fd_table.pid != pid:
        ppid = pid_fd_table.pid
    elif pid_fd_table.ppid is not None:
        ppid = pid_fd_table.ppid
    else:
        ppid = pid

    assert inode_table[file_info[0]][0] == filename

    if offset:    # pread(): the file offset is not changed.
        start_offset = offset
    else:    # read(): offset update
        start_offset = file_info[3]
        file_info[3] = int(start_offset) + int(length)

        # update if current_offset is greater than previous file_size
        if inode_table[file_info[0]][1] < file_info[3]:
            inode_table[file_info[0]][1] = file_info[3]

    return (pid, ppid, fd, start_offset, length, file_info[0])

# write file
def write_access(pid, fd, length, flag, offset=None):
    pid_fd_table = process_dict[pid]
    oftid = pid_fd_table.fd_oft[fd]
    file_info = open_file_table.get_oft_fio(oftid)    # [inode, ref_count, flag, offset]

    if pid_fd_table.pid != pid:
        ppid = pid_fd_table.pid
    elif pid_fd_table.ppid is not None:
        ppid = pid_fd_table.ppid
    else:
        ppid = pid

    for k, v in inode_table.items():
        if (k == file_info[0]):
            max_offset = v[1] 

    if file_info[2] == 'O_APPEND':
        start_offset = max_offset
    else:
        if offset:    # pwrite()
            start_offset = offset
        else:    # write()
            start_offset = file_info[3]

    file_size = int(inode_table[file_info[0]][1]);  length = int(length);   start_offset = int(start_offset)
    if (not offset) or (file_info[2]=='O_APPEND'):    # write(): offset update / pwrite(): the file offset is not changed.
        # update if current_offset is greater than previous file_size
        if file_size < start_offset + length:
            inode_table[file_info[0]][1] = start_offset + length
        if not offset:
            file_info[3] = start_offset + length

    return (pid, ppid, fd, start_offset, length, file_info[0])

def update_fdTable_offset(pid, fd, offset, flag, offset_length):    # syscall 'lseek()'
    pid_fd_table = process_dict[pid]
    oftid = pid_fd_table.fd_oft[fd]
    open_file_table.set_oft_fio_offset(oftid=oftid, offset=offset)

    offset = int(offset);   offset_length = int(offset_length)
    if 'SEEK_END' in flag:
        # update file_size
        if inode_table[open_file_table.file_info[oftid][0]][1] < offset + offset_length:
            inode_table[open_file_table.file_info[oftid][0]][1] = offset + offset_length

#-----
# for convenience
def print_all_table():
    print("--------------------------")
    print("***INODE_TABLE*** {'inode':['filename', file_size]}")
    print(inode_table)
    print("***PROCESS_DICT*** pid {'fd':'oftid'}")
    for k, v in process_dict.items():
        print(k, "==", v.pid, v.fd_oft)
    print("***OPEN_FILE_TABLE*** {'oftid':[inode, ref_count, flag, offset]}")
    print(open_file_table.file_info)
    print("--------------------------")

def find_inode_or_make_fake(filename):
    inode = None
    for k, v in inode_table.items():
        if v[0] == filename:
            inode = str(k)
    if not inode:
        print("unknown file: ", filename)
        random_length = 5
        while ((not inode) or (inode in inode_table.keys())):
            inode = "fake_inode_"+''.join(random.sample(string.ascii_lowercase, random_length))
        inode_table[inode] = [filename, 0]
        inf.write(filename+","+inode+"\n")

    return inode

inode_table['stdin'] = ['stdin', 0]
inode_table['stdout'] = ['stdout', 0]
inode_table['stderr'] = ['stderr', 0]

#-----
def file_trace(line):
    line = line.strip('\n')  # remove '\n'
    line = line.replace("'", "")

    # separate the syscall log by comma
    s = line.split(',')

    #---
    if s[C_op] == 'open' or s[C_op] == 'openat' or s[C_op] == 'creat' or s[C_op] == 'memfd_create':
        if '=>' in s[C_filename]:
            filename = s[C_filename][s[C_filename].rfind('=>')+2:]
        else:
            filename = s[C_filename]
        
        # find inode from inode_table
        inode = find_inode_or_make_fake(filename=filename)
        insert_fdTable(pid=s[C_pid], fd=s[C_fd], inode=inode, flag=s[C_flags], offset=None)

    elif s[C_op] == 'lseek':
        try:
            update_fdTable_offset(pid=s[C_pid], fd=s[C_fd], offset=s[C_offset], flag=s[C_flags], offset_length=s[C_length])
        except KeyError as e:
            print("lseek", e, ":", line, file=ef)
            inode = find_inode_or_make_fake(filename=s[C_filename])
            insert_fdTable(pid=s[C_pid], fd=s[C_fd], inode=inode, flag=None, offset=None)

            update_fdTable_offset(pid=s[C_pid], fd=s[C_fd], offset=s[C_offset], flag=s[C_flags], offset_length=s[C_length])
            return 0

    # some files read/write after running syscall 'close'
    elif s[C_op] == 'close':
        try:
            remove_fdTable(pid=s[C_pid], fd=s[C_fd])
        except KeyError as e:    # already closed
            print('close', e, ':', line, file=ef)
            return 0

    elif s[C_op] == 'fork' or s[C_op] == 'clone':
        if 'CLONE_FILES' in s[C_flags]:
            share_fdTable(ppid=s[C_pid], cpid=s[C_cpid])
        else:
            copy_fdTable(ppid=s[C_pid], cpid=s[C_cpid])

    elif s[C_op] == 'read' or s[C_op] == 'pread64':
        if s[C_op]=='read':
            s[C_offset]=None
        try:
            (pid, ppid, fd, start_offset, length, inode) = read_access(pid=s[C_pid], fd=s[C_fd], length=s[C_length], flag=s[C_flags], offset=s[C_offset], filename=s[C_filename])
        except Exception as e:
            print("read/pread64", e, ":", line, file=ef)
            # fd==0:stdin, fd==1:stdout, fd==2:stderr
            if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
                insert_fdTable(pid=s[C_pid], fd=0, inode='stdin', flag=None, offset=None)
                insert_fdTable(pid=s[C_pid], fd=1, inode='stdout', flag=None, offset=None)
                insert_fdTable(pid=s[C_pid], fd=2, inode='stderr', flag=None, offset=None)
            else:
                inode = find_inode_or_make_fake(filename=s[C_filename])
                insert_fdTable(pid=s[C_pid], fd=s[C_fd], inode=inode, flag=None, offset=None)
            (pid, ppid, fd, start_offset, length, inode) = read_access(pid=s[C_pid], fd=s[C_fd], length=s[C_length], flag=s[C_flags], offset=s[C_offset], filename=s[C_filename])

        #---
        wlines = s[C_time] + "," + s[C_pid] + "," + str(ppid) + "," + "read" + "," + s[C_fd] + "," + str(start_offset) + "," + str(length) + "," + inode
        return wlines

    elif s[C_op] == 'write' or s[C_op] == 'pwrite64':
        if s[C_op]=='write':
            s[C_offset]=None
        try:
            (pid, ppid, fd, start_offset, length, inode) = write_access(pid=s[C_pid], fd=s[C_fd], length=s[C_length], flag=s[C_flags], offset=s[C_offset])
        except KeyError as e:
            print("write/pwrite64", e, ":", line, file=ef)
            # fd==0:stdin, fd==1:stdout, fd==2:stderr
            if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
                insert_fdTable(pid=s[C_pid], fd='0', inode='stdin', flag=None, offset=None)
                insert_fdTable(pid=s[C_pid], fd='1', inode='stdout', flag=None, offset=None)
                insert_fdTable(pid=s[C_pid], fd='2', inode='stderr', flag=None, offset=None)
            else:
                inode = find_inode_or_make_fake(filename=s[C_filename])
                insert_fdTable(pid=s[C_pid], fd=s[C_fd], inode=inode, flag=None, offset=None)
            (pid, ppid, fd, start_offset, length, inode) = write_access(pid=s[C_pid], fd=s[C_fd], length=s[C_length], flag=s[C_flags], offset=s[C_offset])

        #---
        wlines = s[C_time] + "," + s[C_pid] + "," + str(ppid) + "," + "write" + "," + s[C_fd] + "," + str(start_offset) + "," + str(length) + "," + inode
        return wlines

    elif s[C_op] == 'dup' or s[C_op] == 'dup2' or s[C_op] == 'dup3':
        fd = s[C_fd].split('||')
        filename = s[C_filename].split('||')
        try:
            copy_fd(pid=s[C_pid], oldfd=fd[0], newfd=fd[1])
        except KeyError as e:
            print("dup/dup2/dup3", e, ":", line, file=ef)
            inode = find_inode_or_make_fake(filename=filename[0])
            insert_fdTable(pid=s[C_pid], fd=fd[0], inode=inode, flag=None, offset=None)
            copy_fd(pid=s[C_pid], oldfd=fd[0], newfd=fd[1])

    elif s[C_op] == 'fcntl' and s[C_flags] == 'F_DUPFD':  # only for 'F_DUPFD' 
        fd = s[C_fd].split('||')
        filename = s[C_filename].split('||')
        try:
            copy_fd(pid=s[C_pid], oldfd=fd[0], newfd=fd[1])
        except KeyError as e:
            print("fcntl", e, ":", line, file=ef)
            inode = find_inode_or_make_fake(filename=filename[0])
            insert_fdTable(pid=s[C_pid], fd=fd[0], inode=inode, flag=None, offset=None)
            copy_fd(pid=s[C_pid], oldfd=fd[0], newfd=fd[1])

    elif s[C_op] == 'pipe' or s[C_op] == 'pipe2':
        fd = s[C_fd].split('||')
        pipe = s[C_filename].split('||')
        filenames = [f[0] for f in inode_table.values()]

        # inode_table
        if not pipe[0] in filenames:
            read_file_info = [pipe[0], 0]    # ['read pipe', 0]
            inode_table[pipe[0]] = read_file_info
        if not pipe[1] in filenames:
            write_file_info = [pipe[1], 0]    # ['write pipe', 0]
            inode_table[pipe[1]] = write_file_info

        if not fd[0] in process_dict[s[C_pid]].fd_oft.keys():
            insert_fdTable(pid=s[C_pid], fd=fd[0], inode=pipe[0])
        if not fd[1] in process_dict[s[C_pid]].fd_oft.keys():
            insert_fdTable(pid=s[C_pid], fd=fd[1], inode=pipe[1])
    
    elif s[C_op] == 'eventfd' or s[C_op] == 'eventfd2':
        filenames = [f[0] for f in inode_table.values()]

        # inode_table
        if not s[C_filename] in filenames:
            inode_table[s[C_filename]] = [s[C_filename], 0]    # ['event fd', s[C_length]]

        if not s[C_fd] in process_dict[s[C_pid]].fd_oft.keys():
            insert_fdTable(pid=s[C_pid], fd=s[C_fd], inode=s[C_filename])

    elif s[C_op] == 'socket':
        filenames = [f[0] for f in inode_table.values()]

        # inode_table
        if not s[C_filename] in filenames:
            inode_table[s[C_filename]] = [s[C_filename], 0]    # ['socket fd', 0]

        if not s[C_fd] in process_dict[s[C_pid]].fd_oft.keys():
            insert_fdTable(pid=s[C_pid], fd=s[C_fd], inode=s[C_filename])

    elif s[C_op] == 'socketpair':
        fd = s[C_fd].split('||')
        socket = s[C_filename].split('||')
        filenames = [f[0] for f in inode_table.values()]

        # inode_table
        if not socket[0] in filenames:
            sp0_info = [socket[0], 0]    # ['socket pair 0', 0]
            inode_table[socket[0]] = sp0_info
        if not socket[1] in filenames:
            sp1_info = [socket[1], 0]    # ['socket pair 1', 0]
            inode_table[socket[1]] = sp1_info

        if not fd[0] in process_dict[s[C_pid]].fd_oft.keys():
            insert_fdTable(pid=s[C_pid], fd=fd[0], inode=socket[0])
        if not fd[1] in process_dict[s[C_pid]].fd_oft.keys():
            insert_fdTable(pid=s[C_pid], fd=fd[1], inode=socket[1])

    return 1

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')
    parser.add_argument("--filename_inode", "-f", metavar='Fi', type=str,
                        nargs='?', default='file-inode.txt', help='filename-inode file')

    args = parser.parse_args()

    ef = open(args.output+'.err', 'w')

    # fill inode_dict
    inode_df = pd.read_csv(args.filename_inode, header=0)
    filename = inode_df['filename']
    inode = inode_df['inode']
    for k, v in zip(inode, filename):
        inode_table[str(k)] = [v, 0]

    # column
    C_time = 0
    C_pid = 1
    C_op = 2    # operation
    C_cpid = 3    # child process pid
    C_fd = 4
    C_offset = 5
    C_flags = 6
    C_length = 7
    C_mem = 8     # memory address
    C_filename = 9    # filename
    C_ino = 10   # inode

    ### 3. track syscalls line by line
    rf = open(args.input, 'r')
    rlines = rf.readlines()
    inf = open(args.filename_inode, 'a')
    wf = open(args.output, 'w')

    for _, line in enumerate(rlines):
        ret = file_trace(line=line)
        if ret == 0 or ret == 1:
            continue
        else:
            wf.write(ret + "\n")

    rf.close()
    wf.close()
    inf.close()
    ef.close()
    #print_all_table()