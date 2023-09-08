import argparse
import csv
import copy
import random, string

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')
parser.add_argument("--filename_inode", "-f", metavar='Fi', type=str,
                    nargs='?', default='file-inode.txt', help='filename-inode file')

args = parser.parse_args()

ef = open(args.output+'.err', 'w')

### 1. get filename-inode pair
inode_table = dict()    # {'inode': [filename, file_size]}  ### 원래는 {'inode': [filename, ref_count]}
"""with open(args.filename_inode, 'r') as r:
    reader = csv.reader(r, delimiter=',')
    for row in reader:
        try:
            filename, inode = row
            inode_table[inode] = [filename, 0]
        except ValueError:
            print("get filename-inode error: ", row, file=ef)"""

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

        '''current_max_ofset = self.file_info[oftid][4]
        self.file_info[oftid][4] = offset if offset > current_max_ofset else current_max_ofset'''

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

### 3. objects for trace read/write operations
class fdTable:    # File descriptor table of process
    def __init__(self, pid):
        self.pid = pid
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

#-----
process_dict = dict()    # {'pid': fdTable}
open_file_table = openFileTable()

# open new file in a process
def insert_fdTable(pid, fd, inode, flag=None, offset=None):
    '''if filename not in inode_table.keys():
        print("File '", filename, "' is not in inode table", sep='')
        inode_table[filename] = "unknown file"'''

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

    for k, v in cpid_fd_table.fd_oft.items():
        open_file_table.file_info[v][1] += 1

    process_dict[cpid] = cpid_fd_table

# share same file descriptor table ('CLONE_FILES' flag)
def share_fdTable(ppid, cpid):
    ppid_fd_table = process_dict[ppid]
    cpid_fd_table = ppid_fd_table

    #for k, v in cpid_fd_table.fd_oft.items():
    #    open_file_table.file_info[v][1] += 1

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

    assert inode_table[file_info[0]][0] == filename

    if offset:    # pread(): the file offset is not changed.
        start_offset = offset
    else:    # read(): offset update
        start_offset = file_info[3]
        file_info[3] = int(start_offset) + int(length)

        '''for k, v in inode_table.items():    # update if current_offset is greater than previous file_size
            if (v[0] == file_info[0]) and (v[1] < file_info[3]):
                v[1] = file_info[3]'''
        if inode_table[file_info[0]][1] < file_info[3]:
            inode_table[file_info[0]][1] = file_info[3]

    return (pid, fd, start_offset, length, file_info[0])

# write file
def write_access(pid, fd, length, flag, offset=None):
    pid_fd_table = process_dict[pid]
    oftid = pid_fd_table.fd_oft[fd]
    file_info = open_file_table.get_oft_fio(oftid)    # [inode, ref_count, flag, offset]
    
    for k, v in inode_table.items():
        if (v[0] == file_info[0]):
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
        '''for k, v in inode_table.items():
            if (v[0] == file_info[0]) and (v[1] < (start_offset + length)):    # update if current_offset is greater than previous file_size
                v[1] = start_offset + length'''
        if file_size < start_offset + length:
            inode_table[file_info[0]][1] = start_offset + length
        if not offset:
            file_info[3] = start_offset + length

    return (pid, fd, start_offset, length, file_info[0])

def update_fdTable_offset(pid, fd, offset, flag, offset_length):    # syscall 'lseek()'
    pid_fd_table = process_dict[pid]
    oftid = pid_fd_table.fd_oft[fd]
    open_file_table.set_oft_fio_offset(oftid=oftid, offset=offset)

    offset = int(offset);   offset_length = int(offset_length)
    if 'SEEK_END' in flag:
        '''for k, v in inode_table.items():
            if (v[0] == open_file_table.file_info[0]) and (v[1] < (offset + offset_length)):    # update file_size
                v[1] = offset + offset_length'''
        if inode_table[open_file_table.file_info[0]][1] < offset + offset_length:
            inode_table[open_file_table.file_info[0]][1] = offset + offset_length

def print_all_table():
    print("--------------------------")
    print("***INODE_TABLE*** {'filename':[inode, file_size]}")
    print(inode_table)
    print("***PROCESS_DICT*** pid {'fd':'oftid'}")
    for k, v in process_dict.items():
        print(k, "==", v.pid, v.fd_oft)
    print("***OPEN_FILE_TABLE*** {'oftid':[inode, ref_count, flag, offset]}")
    print(open_file_table.file_info)
    print("--------------------------")

def insert_fake_inode(pid, fd, filename, flag):
    inode = None
    random_length = 5
    while ((not inode) or (inode in inode_table.keys())):
        inode = "fake_inode_"+''.join(random.sample(string.ascii_lowercase, random_length))
    inode_table[inode] = [filename, 0]
    insert_fdTable(pid=pid, fd=fd, inode=inode, flag=flag, offset=None)

    return inode

inode_table['stdin'] = ['stdin', 0]
inode_table['stdout'] = ['stdout', 0]
inode_table['stderr'] = ['stderr', 0]
