import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument('input', metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument('output', metavar='O', type=str, nargs='?', default='output.txt', help='output file')
parser.add_argument('filename_inode', metavar='Fi', type=str, nargs='?', default='file-inode.txt', help='filename-inode file')

args = parser.parse_args()
#print(args.input, args.output)

### 1. get filename-inode pair
d = dict()
with open(args.filename_inode, 'r') as r:
  try:
    reader = csv.reader(r, delimiter=',')
    for row in reader:
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

for line in rlines:
    line = line.strip("\n") # remove '\n'

    # separate the syscall log by comma
    s = line.split(',')
    
    # column
    C_time=0
    C_pid=1
    C_op=2    # operation
    C_cpid=3    # child process pid
    C_fd=4
    C_offset=5
    C_length=6
    C_mem=7     # memory address
    C_flname=8    # filename
    C_ino=9   # inode
    
    ###open -> file이름으로 inode찾기 -> {pid,fd:[inode,offset]}
    ###lseek -> pid,fd로 offset찾기&inode매칭 -> ppid,fd로 inode매칭(offset은???)...하지 말고 fork 나오면 dict도 fork하자.
    ###      -> 실행중인 프로세스를 붙여서 했을 경우, ppid,fd도 inode 안 나올 수 있음 -> 문자열 inode 임의로 만들자. (이렇게 하면 재참조는 못 봄)

    #---
    if s[C_op]=='open' or s[C_op]=='openat' or s[C_op]=='creat':
        file_info = list()
        #file_info.append(s[8])  # s[8]:filename
        inode = d[s[C_flname].strip('"')]
        file_info.append(inode)
        file_info.append(0) # offset
        fio_info[s[C_pid]+","+s[C_fd]] = file_info    # s[1]:pid, s[4]:fd
    
    elif s[C_op]=='lseek':
        file_info = fio_info.pop(s[C_pid]+","+s[C_fd])    # s[1]:pid, s[4]:fd
        file_info[C_pid] = int(s[C_offset])   # s[5]:offset
        fio_info[s[C_pid]+","+s[C_fd]] = file_info
    
#    """some files read/write after running syscall 'close'."""
#    elif s[2]=='close':
#        try:
#            _ = fio_info.pop(s[1]+","+s[3])    # s[1]:pid, s[3]:fd
#        except KeyError:    # already closed
#            continue
    
    elif s[C_op]=='fork' or s[C_op]=='clone':
        ppid[s[C_cpid]] = s[C_pid]
        #print(ppid)

    elif s[C_op]=='read' or s[C_op]=='write':
        try:
            file_info = fio_info.pop(s[C_pid]+","+s[C_fd])    # s[1]:pid, s[4]:fd
            offset = int(file_info[1])
            #---
            wlines = s[C_time] + "," + s[C_pid] + ",," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
            wf.write(wlines + "\n")
            #---
            file_info[1] = offset + int(s[C_length])    # update offset
            fio_info[s[C_pid]+","+s[C_fd]] = file_info
        except KeyError:
            # 1. fd==0:stdin, fd==1:stdout, fd==2:stderr
            if s[C_fd]=='0' or s[C_fd]=='1' or s[C_fd]=='2':
                wlines = s[C_time] + "," + s[C_pid] + ",," + s[C_op] + "," + s[C_fd] + "," + "0," + s[C_length]
                wf.write(wlines + "\n")
            
            else:
                try:
                    # 2. parent pid
                    p_pid = ppid.pop(s[C_pid])
                    #---
                    file_info = fio_info.pop(p_pid+","+s[C_fd])
                    offset = int(file_info[1])
                    #---
                    wlines = s[C_time] + "," + s[C_pid] + "," + p_pid + "," + s[C_op] + "," + s[C_fd] + "," + str(offset) + "," + s[C_length] + "," + file_info[0]
                    wf.write(wlines + "\n")
                    #---
                    file_info[1] = offset + int(s[C_length])	# update offset
                    file_info[p_pid+","+s[C_fd]] = file_info
                except KeyError:
                    # 3. error case
                    wlines = s[C_time] + "," + s[C_pid] + ",," + s[C_op] + "," + s[C_fd] + "," + "error," + s[C_length]
                    wf.write(wlines + "\n")

    elif s[C_op]=='pread64' or s[C_op]=='pwrite64':
        file_info = fio_info.pop(s[C_pid]+","+s[C_fd])    # s[1]:pid, s[4]:fd
        #---
        wlines = s[C_time] + "," + s[C_pid] + ",," + s[C_op] + "," + s[C_fd] + "," + s[C_offset] + "," + s[C_length] + "," + file_info[0]
        wf.write(wlines + "\n")
        #---
        file_info[1] = int(s[C_offset]) + int(s[C_length])	# update offset
        fio_info[s[C_pid]+","+s[C_fd]] = file_info

rf.close()
wf.close()
