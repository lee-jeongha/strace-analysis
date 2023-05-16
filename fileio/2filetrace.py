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

ef = open(args.output+'.err', 'w')

### 1. get filename-inode pair
inode_dict = dict()
with open(args.filename_inode, 'r') as r:
    reader = csv.reader(r, delimiter=',')
    for row in reader:
        try:
            filename, inode = row
            inode_dict[filename] = inode
        except ValueError:
            print("get filename-inode error: ", row, file=ef)

### 2. objects for trace read/write operations
fd_dict = dict() # {'pid': fdForPid}

class fdForPid(object):
    def __init__(self, pid):
        self.pid = pid
        self.fio_info = dict()   # {'fd': [inode, offset]}

    def set_fio_info(self, fd, file_info):
        self.fio_info[fd] = file_info

    def get_fio_info(self, fd):
        return self.fio_info[fd]

    def pop_fio_info(self, fd):
        file_info = self.fio_info.pop(fd)
        return file_info
    
def create_fdForPid(fd, filename, offset, pid):
    file_info = []
    # create fdForPid object
    if ('pipe:[' in filename) or ('socket:[' in filename):
        inode = filename
    else:
        inode = inode_dict[filename]
    file_info.append(inode)
    file_info.append(offset)   # file_info[1]:offset
    try:
        fd_block = fd_dict[pid]
    except KeyError:
        fd_block = fdForPid(pid)
    fd_block.set_fio_info(fd, file_info)
    fd_dict[pid] = fd_block

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
wf = open(args.output, 'w')

for line in rlines:
    line = line.strip('\n')  # remove '\n'
    line = line.replace('`', '')

    # separate the syscall log by comma
    s = line.split(',')

    #---
    if s[C_op] == 'open' or s[C_op] == 'openat' or s[C_op] == 'creat' or s[C_op] == 'memfd_create':
        file_info = list()

        if '=>' in s[C_filename]:
            s[C_filename] = s[C_filename][s[C_filename].rfind('=>')+2:]
        create_fdForPid(s[C_fd], s[C_filename], 0, s[C_pid])

    elif s[C_op] == 'lseek':
        try:
            fd_block = fd_dict[s[C_pid]]
            file_info = fd_block.pop_fio_info(s[C_fd])
            file_info[1] = int(s[C_offset])   # file_info[1]:offset
            fd_block.set_fio_info(s[C_fd], file_info)
        except KeyError as e:
            print('lseek', e, ':', line, file=ef)
            create_fdForPid(s[C_fd], s[C_filename].strip('`'), int(s[C_offset]), s[C_pid])
            continue

    # some files read/write after running syscall 'close'
    elif s[C_op] == 'close':
        try:
            fd_block = fd_dict[s[C_pid]]
            _ = fd_block.pop_fio_info(s[C_fd])
        except KeyError as e:    # already closed
            print('close', e, ':', line, file=ef)
            continue

    elif s[C_op] == 'fork':
        fd_block = fd_dict[s[C_pid]]
        p_fio_info = fd_block.fio_info.copy()
        
        c_fd_block = fdForPid(s[C_cpid])
        c_fd_block.fio_info = p_fio_info
        
        fd_dict[s[C_cpid]] = c_fd_block
    
    elif s[C_op] == 'clone':
        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:    # clone the process without fd
            fd_block = fdForPid(s[C_cpid])

        if 'CLONE_FILES' in s[C_flags]:
            c_fd_block = fd_block   # copy object
        else:
            p_fio_info = fd_block.fio_info.copy()    # deep copy

            c_fd_block = fdForPid(s[C_cpid])    # create new fdForPid
            c_fd_block.fio_info = p_fio_info
        
        fd_dict[s[C_cpid]] = c_fd_block

    elif s[C_op] == 'read' or s[C_op] == 'write':
        # fd==0:stdin, fd==1:stdout, fd==2:stderr
        if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
            wlines = s[C_time] + "," + s[C_pid] + "," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
            wf.write(wlines + "\n")
            continue
        
        try:
            fd_block = fd_dict[s[C_pid]]
            file_info = fd_block.pop_fio_info(s[C_fd])
        except KeyError as e:
            print('read/write', e, ':', line, file=ef)
            create_fdForPid(s[C_fd], s[C_filename].strip('"'), 0, s[C_pid])
            fd_block = fd_dict[s[C_pid]]
            file_info = fd_block.pop_fio_info(s[C_fd])
        offset = int(file_info[1])
        #---
        wlines = s[C_time] + "," + s[C_pid] + "," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
        wf.write(wlines + "\n")
        #---
        file_info[1] = offset + int(s[C_length])  # update offset
        fd_block.set_fio_info(s[C_fd], file_info)

    elif s[C_op] == 'pread64' or s[C_op] == 'pwrite64':
        # fd==0:stdin, fd==1:stdout, fd==2:stderr
        if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
            wlines = s[C_time] + "," + s[C_pid] + "," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
            wf.write(wlines + "\n")
            continue
        
        fd_block = fd_dict[s[C_pid]]
        try:
            file_info = fd_block.pop_fio_info(s[C_fd])
        except KeyError as e:
            print('pread/pwrite', e, ':', line, file=ef)
            create_fdForPid(s[C_fd], s[C_filename].strip('"'), int(s[C_offset]), s[C_pid])
            file_info = fd_block.pop_fio_info(s[C_fd])
        #---
        wlines = s[C_time] + "," + s[C_pid] + "," + s[C_op] + "," + s[C_fd] + "," + s[C_offset] + "," + s[C_length] + "," + file_info[0]
        wf.write(wlines + "\n")
        #---
        file_info[1] = int(s[C_offset]) + int(s[C_length])  # update offset
        fd_block.set_fio_info(s[C_fd], file_info)

    elif s[C_op] == 'pipe' or s[C_op] == 'pipe2':
        fd = s[C_fd].split('||')

        read_file_info = ['read pipe', 0]
        write_file_info = ['write pipe', 0]

        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:    # make pipe to the process without fd
            fd_block = fdForPid(s[C_pid])
        
        fd_block.set_fio_info(fd[0], read_file_info)
        fd_block.set_fio_info(fd[1], write_file_info)
        fd_dict[s[C_pid]] = fd_block


    elif s[C_op] == 'dup' or s[C_op] == 'dup2' or s[C_op] == 'dup3':
        fd = s[C_fd].split('||')
        filename = s[C_filename].strip('`').split('||')
        try:
            fd_block = fd_dict[s[C_pid]]
            file_info = fd_block.get_fio_info(fd[0])
            fd_block.set_fio_info(fd[1], file_info)
        except KeyError as e:
            print('dup/dup2/dup3', e, ':', line, file=ef)
            fd_block = fdForPid(s[C_pid])
            if fd[0] == '0':
                fd_block.set_fio_info(fd[1], ['stdin', 0])
            elif fd[0] == '1':
                fd_block.set_fio_info(fd[1], ['stdout', 0])
            elif fd[0] == '2':
                fd_block.set_fio_info(fd[1], ['stderr', 0])
            else:
                fd_block.set_fio_info(fd[1], [filename[0], 0])
        
    elif s[C_op] == 'fcntl':
        fd = s[C_fd].split('||')
        filename = s[C_filename].strip('`').split('||')

        fd_block = fd_dict[s[C_pid]]
        try:
            file_info = fd_block.get_fio_info(fd[0])
        except KeyError as e:
            print('fcntl', e, ':', line, file=ef)
            create_fdForPid(fd[0], filename[0], 0, s[C_pid])
            file_info = fd_block.get_fio_info(fd[0])

        fd_block.set_fio_info(fd[1], file_info)

    elif s[C_op] == 'eventfd' or s[C_op] == 'eventfd2':
        file_info = ['event fd', s[C_length]]

        fd_block = fd_dict[s[C_pid]]
        fd_block.set_fio_info(s[C_fd], file_info)

    elif s[C_op] == 'socket':
        file_info = ['socket fd', 0]
        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:
            fd_block = fdForPid(s[C_pid])
        fd_block.set_fio_info(s[C_fd], file_info)

    elif s[C_op] == 'socketpair':
        fd = s[C_fd].split('||')

        sp0_info = ['socket pair 0', 0]
        sp1_info = ['socket pair 1', 0]

        try:
            fd_block = fd_dict[s[C_pid]]
        except KeyError:    # make socket pair to the process without fd
            fd_block = fdForPid(s[C_pid])

        fd_block.set_fio_info(fd[0], sp0_info)
        fd_block.set_fio_info(fd[1], sp1_info)
        fd_dict[s[C_pid]] = fd_block

rf.close()
wf.close()

#print(ppid)
#for v in fd_dict.values():
#    print(v.pid, v.fio_info)
