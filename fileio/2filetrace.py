import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')
parser.add_argument("--filename_inode", "-f", metavar='Fi', type=str,
                    nargs='?', default='file-inode.txt', help='filename-inode file')

args = parser.parse_args()
#print(args.input, args.output)

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

fio_info = dict()   # {'pid, fd': [filename, offset]}
ppid = dict()   # {'pid': 'ppid'}

# column
C_time = 0
C_pid = 1
C_op = 2    # operation
C_cpid = 3    # child process pid
C_fd = 4
C_offset = 5
C_length = 6
C_mem = 7     # memory address
C_flname = 8    # filename
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
    if s[C_op] == 'open' or s[C_op] == 'openat' or s[C_op] == 'creat':
        file_info = list()
        #file_info.append(s[8])  # s[8]:filename
        inode = d[s[C_flname].strip('"')]
        file_info.append(inode)
        file_info.append(0)  # offset
        fio_info[s[C_pid]+","+s[C_fd]] = file_info    # s[1]:pid, s[4]:fd

    elif s[C_op] == 'lseek':
        p_pid = getppid(s[C_pid])
        try:
            # 1. use pid
            file_info = fio_info.pop(s[C_pid]+","+s[C_fd])    # s[1]:pid, s[4]:fd
            file_info[1] = int(s[C_offset])   # file_info[1]:offset
            fio_info[s[C_pid]+","+s[C_fd]] = file_info
        except KeyError as e:
            # 2. error case
            #print('lseek',e)
            continue

#    """some files read/write after running syscall 'close'."""
#    elif s[2]=='close':
#        try:
#            _ = fio_info.pop(s[1]+","+s[3])    # s[1]:pid, s[3]:fd
#        except KeyError:    # already closed
#            continue

    elif s[C_op] == 'fork' or s[C_op] == 'clone':
        ppid[s[C_cpid]] = s[C_pid]
        #print(ppid)
        fd = []
        offset = []
        for key, value in fio_info.items():
            fi = key.split(',')
            if fi[0] == s[C_pid]:  # fi[0]:pid
                fd.append(fi[1])  # fi[1]:fd
                offset.append(value)  # value:[inode,offset]
        for i in range(len(fd)):
            fio_info[s[C_cpid]+","+fd[i]] = offset[i]

    elif s[C_op] == 'read' or s[C_op] == 'write':
        p_pid = getppid(s[C_pid])
        # 1. fd==0:stdin, fd==1:stdout, fd==2:stderr
        if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
            wf.write(wlines + "\n")
            continue
        # 2. use pid
        try:
            file_info = fio_info.pop(s[C_pid]+","+s[C_fd])    # s[1]:pid, s[4]:fd
            offset = int(file_info[1])
            #---
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
            wf.write(wlines + "\n")
            #---
            file_info[1] = offset + int(s[C_length])  # update offset
            fio_info[s[C_pid]+","+s[C_fd]] = file_info

        except KeyError:
            # 3. try to use ppid
            try:  # (p_pid != s[C_pid])
                file_info = fio_info.pop(p_pid+","+s[C_fd])    # s[1]:pid, s[4]:fd
                offset = int(file_info[1])
                #---
                wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
                wf.write(wlines + "\n")
                #---
                file_info[1] = offset + int(s[C_length])  # update offset
                fio_info[s[C_pid]+","+s[C_fd]] = file_info
            # 4. error case
            except KeyError as e:
                wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "error," + s[C_length]
                wf.write(wlines + "\n")
                #print('read/write',e)

    elif s[C_op] == 'pread64' or s[C_op] == 'pwrite64':
        p_pid = getppid(s[C_pid])
        # 1. fd==0:stdin, fd==1:stdout, fd==2:stderr
        if s[C_fd] == '0' or s[C_fd] == '1' or s[C_fd] == '2':
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
            wf.write(wlines + "\n")
            continue
        # 2. use pid
        try:
            file_info = fio_info.pop(s[C_pid]+","+s[C_fd])    # s[1]:pid, s[4]:fd
            #---
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + s[C_offset] + "," + s[C_length] + "," + file_info[0]
            wf.write(wlines + "\n")
            #---
            file_info[1] = int(s[C_offset]) + int(s[C_length])  # update offset
            fio_info[s[C_pid]+","+s[C_fd]] = file_info
        # 3. error case
        except KeyError as e:
            wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + "error," + s[C_length]
            wf.write(wlines + "\n")
            #print('pread/pwrite',e)

rf.close()
wf.close()
