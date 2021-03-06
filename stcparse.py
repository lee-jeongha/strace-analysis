import argparse
import textwrap
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description="strace parser for [read / write / pread64 / pwrite64 / lseek / mmap / munmap / mremap / creat / open / openat / close / stat / fstat / lstat / fork / clone]",
                                 epilog="strace -a1 -s0 -f -C -tt -v -e trace=read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,close,stat,fstat,lstat,fork,clone -o input.txt [program]")

parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')

args = parser.parse_args()
#print(args.input, args.output) #, args.infile)


rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')

un = dict()  # for '<unfinished ...>' log

for line in rlines:
    line = line.strip("\n")  # remove '\n'

    if ('<unfinished' in line):
        # where a strace log is cut off == where the '<unfinished ...' message is started
        pos_end = line.find('<unfinished')
        pid_end = line.find(' ')
        # put pid(key) with strace-log(value) in set 'un'
        pid = line[:pid_end]
        strace = line[:pos_end]
        un[pid] = strace
        continue

    elif ('resumed>' in line):
        # length of string 'resumed>' is 8
        pos_start = line.rfind('resumed>') + 8
        pid_end = line.find(' ')
        # get pid(key) with the front part of strace-log(value) in set 'un'
        pid = line[:pid_end]
        strace = line[pos_start:]
        # concat strace-logs
        if(pid in un):
            line = un[pid] + strace
            #print(line)
            del un[pid]

  # find struct
    if ('{' in line):
        struct_start = line.index('{') + 1
        struct_end = line.index('}')
        struct = line[struct_start:struct_end]
        line = line[:struct_start - 1] + "struct" + line[struct_end + 1:]
        #print(line)

    # separate the syscall command and its parameters by spaces
    line = line.translate(str.maketrans({"(": " ", ",": "", ")": ""}))
    s = line.split(' ')

    # find position of return
    try:
      ret = s.index('=') + 1
    except ValueError:  # '=' is not in list
      continue

    if (s[2] == 'read'):  # On success, the number of bytes read is returned (zero indicates end of file)
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3] + ",," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'write'):
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3] + ",," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'pread64'):
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3] + "," + s[6] + "," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'pwrite64'):
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3] + "," + s[6] + "," + s[ret]
        wf.write(wlines + "\n")

    # returns the resulting offset location as measured in bytes (on error, return -1)
    elif (s[2] == 'lseek') and s[ret] != '-1':
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3] + "," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'openat') and s[ret] != '-1':  # on error, return -1
        # blank in filename
        start = line.find('"')
        end = line.rfind('"')
        filename = line[start:end+1]

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[ret] + ",,,," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'open') and s[ret] != '-1':  # on error, return -1
        # blank in filename
        start = line.find('"')
        end = line.rfind('"')
        filename = line[start:end+1]

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[ret] + ",,,," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'close') and s[ret] == '0':  # on success
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3]
        wf.write(wlines + "\n")

    elif (s[2] == 'create') and s[ret] != '-1':  # on error, return -1
        # blank in filename
        start = line.find('"')
        end = line.rfind('"')
        filename = line[start:end+1]

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[ret] + ",,,," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'mmap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[7] + "," + s[8] + "," + s[4] + "," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'munmap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,," + s[4] + "," + s[3]
        wf.write(wlines + "\n")

    elif (s[2] == 'mremap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,," + s[5] + "," + s[3] + ":" + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'stat') and s[ret] != '-1':
        #find struct
        struct = struct.split('st_')
        struct = struct[1:]
        struct = [struct[i].strip(', ') for i in range(len(struct))]
        struct = ['st_' + struct[i] for i in range(len(struct))]
        #print(struct)

        # blank in filename
        start = line.find('"')
        end = line.rfind('"')
        filename = line[start:end+1]

        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,,," + filename + "," + struct[1][7:]   # length of 'st_ino=' == 7
        wf.write(wlines + "\n")
        struct = ''  # flush struct

    elif (s[2] == 'fstat') and s[ret] != '-1':
        try:
            #find struct
            struct = struct.split('st_')
            struct = struct[1:]
            struct = [struct[i].strip(', ') for i in range(len(struct))]
            struct = ['st_' + struct[i] for i in range(len(struct))]
            #print(struct)

            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[3] + ",,,,," + struct[1][7:]   # length of 'st_ino=' == 7
            wf.write(wlines + "\n")

        except IndexError:
            print(struct)
            print(line)

        struct = ''  # flush struct

    elif (s[2] == 'lstat') and s[ret] != '-1':
        #find struct
        struct = struct.split('st_')
        struct = struct[1:]
        struct = [struct[i].strip(', ') for i in range(len(struct))]
        struct = ['st_' + struct[i] for i in range(len(struct))]
        #print(struct)

        # blank in filename
        start = line.find('"')
        end = line.rfind('"')
        filename = line[start:end+1]

        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,,," + filename + "," + struct[1][8:]   # length of 'st_ino=' == 7
        wf.write(wlines + "\n")
        struct = ''  # flush struct

    elif (s[2] == 'clone' or s[2] == 'fork'):
        wlines = s[1] + "," + s[0] + "," + s[2] + "," + s[ret]
        wf.write(wlines + "\n")

    '''
    #elif s[1].startswith('readlink'):	# 433264 readlink("/proc/self/exe", "/usr/bin/python3.8", 4095) = 18
    #  wlines = "89  " + s[2][:-1] + " " + str(int(s[3][:-1], 16)) + " " + s[1][9:-1] + " " + str(int(s[5], 16))
    #  wf.write(wlines + "\n")

    #elif s[1].startswith('readlinkat'):	# 433264 readlinkat(0x3, "/proc/self/exe", "/usr/bin/python3.8", 4095) = 18
    #  wlines = "267 " + str(int(s[1][11:-2], 16)) + " " + s[3][:-1] + " " + str(int(s[4][:-1], 16)) + " " + s[2][:-1] + " " + str(int(s[6], 16))
    #  wf.write(wlines + "\n")
    '''

rf.close()
wf.close()
