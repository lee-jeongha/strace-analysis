import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input', metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument('output', metavar='O', type=str, nargs='?', default='output.txt', help='output file')

args = parser.parse_args()
#print(args.input, args.output)

rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')

#[time, pid, syscall, fd, offset, length, address(inode), filename]
#read, write, pread64, pwrite64, open, openat, creat, close, lseek
#[pid, fd, filename, offset]
#read/write, ofset, length, filename

fio_info = dict()   # {'pid, fd': [filename, offset]}

for line in rlines:
    line = line.strip("\n") # remove '\n'

    # separate the syscall log by comma
    s = line.split(',')
    
    #
    if s[2]=='open' or s[2]=='openat' or s[2]=='creat':
        file_info = list()
        #file_info.append(s[3])  # s[3]:fd
        file_info.append(s[7])  # s[7]:filename
        file_info.append(0) # offset
        fio_info[s[1]+","+s[3]] = file_info
    
    elif s[2]=='lseek':
        file_info = fio_info.pop(s[1]+","+s[3])    # s[1]:pid, s[3]:fd
        file_info[1] = int(s[4])   # s[4]:offset
        fio_info[s[1]+","+s[3]] = file_info
    
    elif s[2]=='close':
        try:
            _ = fio_info.pop(s[1]+","+s[3])    # s[1]:pid, s[3]:fd
        except KeyError:
            continue

    elif s[2]=='read' or s[2]=='write':
        print(fio_info)
        try:
            file_info = fio_info.pop(s[1]+","+s[3])    # s[1]:pid, s[3]:fd
            offset = int(file_info[1])
            #---
            wlines = s[0] + "," + s[1] + "," + s[2] + "," + s[3] + "," + str(offset) + "," + s[5] + "," + file_info[0]
            wf.write(wlines + "\n")
            #---
            file_info[1] = offset + int(s[5])    # update offset
            fio_info[s[1]+","+s[3]] = file_info
        except KeyError:
            wlines = s[0] + "," + s[1] + "," + s[2] + "," + s[3] + "," + "error"
            wf.write(wlines + "\n")

    elif s[2]=='pread64' or s[2]=='pwrite64':
        file_info = fio_info.pop(s[1]+","+s[3])    # s[1]:pid, s[3]:fd
        #---
        wlines = line + "," + file_info[0]
        wf.write(wlines + "\n")
        #---
        file_info[1] = int(s[4]) + int(s[5])
        fio_info[s[1]+","+s[3]] = file_info

rf.close()
wf.close()
