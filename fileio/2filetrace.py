import argparse
import csv
import copy

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')
parser.add_argument("--filename_inode", "-f", metavar='Fi', type=str,
                    nargs='?', default='file-inode.txt', help='filename-inode file')

args = parser.parse_args()

### 1. get filename-inode pair
d = dict()
with open(args.filename_inode, 'r') as r:
    reader = csv.reader(r, delimiter=',')
    for row in reader:
        try:
            filename, inode = row
            d[filename] = inode
        except ValueError:
            print(row)
#print(d)


### 2. track read/write syscalls
rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')

#[time, pid, syscall, fd, offset, length, address(inode), filename]
#read, write, pread64, pwrite64, open, openat, creat, close, lseek
#[pid, fd, filename, offset]
#read/write, ofset, length, filename

ppid = dict()   # {'pid': 'ppid'}
fd_dict = dict() # {'pid': fdForPid}

class fdForPid(object):
    def __init__(self, pid):
        self.pid = pid
        self.fio_info = dict()   # {'fd': [filename, offset]}
        #self.ppid = list()   # ['ppid']

    def set_fio_info(self, fd, file_info):
        self.fio_info[fd] = file_info

    def get_fio_info(self, fd):
        return self.fio_info[fd]

    def pop_fio_info(self, fd):
        file_info = self.fio_info.pop(fd)
        return file_info

# column
C_time = 0
C_pid = 1
C_op = 2    # operation
C_cpid = 3    # child process pid
C_fd = 4
C_offset_flags = 5
C_length = 6
C_mem = 7     # memory address
C_filename = 8    # filename
C_ino = 9   # inode


# get parent pid
def getppid(pid):
    try:
        p = ppid[pid]
        return p
    except KeyError:
        return pid


for line in rlines:
    line = line.strip("\n")  # remove '\n'

    # separate the syscall log by comma
    s = line.split(',')

    #---
    if s[C_op] == 'open' or s[C_op] == 'openat' or s[C_op] == 'creat' or s[C_op] == 'memfd_create':
        file_info = list()

        inode = d[s[C_filename].strip('"')]
        file_info.append(inode)
        file_info.append(0)  # offset

        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:
            fd_block = fdForPid(s[C_pid])
        fd_block.set_fio_info(s[C_fd], file_info)
        fd_dict[s[C_pid]] = fd_block

    elif s[C_op] == 'lseek':
        p_pid = getppid(s[C_pid])
        try:
            # 1. use pid
            fd_block = fd_dict[s[C_pid]]
            file_info = fd_block.pop_fio_info(s[C_fd])
            file_info[1] = int(s[C_offset_flags])   # file_info[1]:offset
            fd_block.set_fio_info(s[C_fd], file_info)
        except KeyError as e:
            # 2. error case
            print('lseek', e, ':', line)
            continue

    # some files read/write after running syscall 'close'
    elif s[C_op] == 'close':
        try:
            fd_block = fd_dict[s[C_pid]]
            _ = fd_block.pop_fio_info(s[C_fd])
        except KeyError as e:    # already closed
            print('close', e, ':', line)
            continue

    elif s[C_op] == 'fork':
        ppid[s[C_cpid]] = s[C_pid]

        fd_block = fd_dict[s[C_pid]]
        p_fio_info = fd_block.fio_info.copy()
        
        c_fd_block = fdForPid(s[C_cpid])
        c_fd_block.fio_info = p_fio_info
        
        fd_dict[s[C_cpid]] = c_fd_block
    
    elif s[C_op] == 'clone':
        ppid[s[C_cpid]] = s[C_pid]

        if 'CLONE_FILES' in s[C_offset_flags]:
            c_fd_block = fd_dict[s[C_pid]]

        else:
            fd_block = fd_dict[s[C_pid]]
            p_fio_info = fd_block.fio_info.copy()
        
            c_fd_block = fdForPid(s[C_cpid])
            c_fd_block.fio_info = p_fio_info
        
        fd_dict[s[C_cpid]] = c_fd_block

    elif s[C_op] == 'read' or s[C_op] == 'write':
        p_pid = getppid(s[C_pid])
        # 1. fd==0:stdin, fd==1:stdout, fd==2:stderr
        if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
            wf.write(wlines + "\n")
            continue
        # 2. use pid
        fd_block = fd_dict[s[C_pid]]
        try:
            file_info = fd_block.pop_fio_info(s[C_fd])
            offset = int(file_info[1])
            #---
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
            wf.write(wlines + "\n")
            #---
            file_info[1] = offset + int(s[C_length])  # update offset
            fd_block.set_fio_info(s[C_fd], file_info)

        except KeyError:
            # 3. try to use ppid
            try:  # (p_pid != s[C_pid])
                fd_block = fd_dict[p_pid]
                file_info = fd_block.pop_fio_info(s[C_fd])
                offset = int(file_info[1])
                #---
                wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
                wf.write(wlines + "\n")
                #---
                file_info[1] = offset + int(s[C_length])  # update offset
                fd_block.set_fio_info(s[C_fd], file_info)
            # 4. error case
            except KeyError as e:
                wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "error," + s[C_length]
                wf.write(wlines + "\n")
                print('read/write', e, ':', line)

    elif s[C_op] == 'pread64' or s[C_op] == 'pwrite64':
        p_pid = getppid(s[C_pid])
        # 1. fd==0:stdin, fd==1:stdout, fd==2:stderr
        if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
            wf.write(wlines + "\n")
            continue
        # 2. use pid
        fd_block = fd_dict[s[C_pid]]
        try:
            file_info = fd_block.pop_fio_info(s[C_fd])
            #---
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + s[C_offset_flags] + "," + s[C_length] + "," + file_info[0]
            wf.write(wlines + "\n")
            #---
            file_info[1] = int(s[C_offset_flags]) + int(s[C_length])  # update offset
            fd_block.set_fio_info(s[C_fd], file_info)
        # 3. error case
        except KeyError as e:
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "error," + s[C_length]
            wf.write(wlines + "\n")
            print('pread/pwrite', e, ':', line)

    elif s[C_op] == 'pipe' or s[C_op] == 'pipe2':
        fd = s[C_fd].split(':')

        read_file_info = ['read pipe', 0]
        write_file_info = ['write pipe', 0]

        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:
            fd_block = fdForPid(s[C_pid])
        fd_block.set_fio_info(fd[0], read_file_info)
        fd_block.set_fio_info(fd[1], write_file_info)
        fd_dict[s[C_pid]] = fd_block


    elif s[C_op] == 'dup' or s[C_op] == 'dup2' or s[C_op] == 'dup3':
        fd = s[C_fd].split(':')

        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:
            fd_block = fdForPid(s[C_pid])

        try:
            file_info = fd_block.get_fio_info(fd[0])
            fd_block.set_fio_info(fd[1], file_info)
        except KeyError as e:
            print('dup/dup2/dup3', e, ':', line)
            if fd[0] == '0':
                fd_block.set_fio_info(fd[1], ['stdin', 0])
            elif fd[0] == '1':
                fd_block.set_fio_info(fd[1], ['stdout', 0])
            elif fd[0] == '2':
                fd_block.set_fio_info(fd[1], ['stderr', 0])

    elif s[C_op] == 'fcntl':
        fd = s[C_fd].split(':')

        fd_block = fd_dict[s[C_pid]]
        file_info = fd_block.get_fio_info(fd[0])
        fd_block.set_fio_info(fd[1], file_info)

    elif s[C_op] == 'eventfd' or s[C_op] == 'eventfd2':
        file_info = ['event fd', s[C_offset_flags]]

        fd_block = fd_dict[s[C_pid]]
        fd_block.set_fio_info(s[C_fd], file_info)

    elif s[C_op] == 'socket':
        file_info = ['socket fd', 0]

        fd_block = fd_dict[s[C_pid]]
        fd_block.set_fio_info(s[C_fd], file_info)

    elif s[C_op] == 'socketpair':
        fd = s[C_fd].split(':')

        sp0_info = ['socket pair 0', 0]
        sp1_info = ['socket pair 1', 0]

        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:
            fd_block = fdForPid(s[C_pid])
        fd_block.set_fio_info(fd[0], sp0_info)
        fd_block.set_fio_info(fd[1], sp1_info)
        fd_dict[s[C_pid]] = fd_block

rf.close()
wf.close()