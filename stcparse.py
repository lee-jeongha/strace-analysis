import argparse
import textwrap
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description="strace parser for [read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,memfd_create,close,stat,fstat,lstat,fork,clone,socket,socketpair,pipe,pipe2,dup,dup2,dup3,fcntl,eventfd,eventfd2]",
                                 epilog="strace -a1 -s0 -f -C -tt -v -yy -z -o input.txt [program]")

parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')

args = parser.parse_args()

def get_fd_filename(fd_filename):
    start = fd_filename.find('<')
    end = fd_filename.rfind('>')

    fd = fd_filename[:start]
    filename = '"' + fd_filename[start+1:end] + '"'

    return str(fd), filename

def check_brackets(line, bracket):
    #bracket_left = [i for i, value in enumerate(line) if value == bracket[0]]
    #bracket_right = [i for i, value in enumerate(line) if value == bracket[1]]
    check = 0
    bracket_left = []
    bracket_right = []
    for i in range(len(line)):
        if line[i] == bracket[0]:
            check += 1
            if check == 1:
                bracket_left.append(i)
        elif line[i] == bracket[1]:
            check -= 1
            if check == 0:
                bracket_right.append(i)
    #line = line.translate(str.maketrans({" ": "_"}))
    return bracket_left, bracket_right

rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')

un = dict()  # for '<unfinished ...>' log

for line in rlines:
    line = line.strip("\n")  # remove '\n'
    line = line.replace('  ', ' ')

    # For '<unfinished ...>' or '<... ~~~ resumed>' case
    if ('<unfinished' in line):
        # where a strace log is cut off == where the '<unfinished ...' message is started
        unf_idx = line.find('<unfinished')
        line = line[:unf_idx - 1]

        # split into 3 chunks
        split_line = line.split(sep=' ', maxsplit=2)
        pid = split_line[0]
        time = split_line[1]
        strace_log = split_line[2]

        # put pid(key) with strace-log(value) in set 'un'
        un[pid] = strace_log
        continue

    elif ('resumed>' in line):
        split_line = line.split(sep=' ', maxsplit=2)
        pid = split_line[0]
        time = split_line[1]
        strace_log = split_line[2]

        # length of string 'resumed>' is 8
        resm_idx = strace_log.rfind('resumed>') + 8
        # get pid(key) with the front part of strace-log(value) in set 'un'
        strace_log = strace_log[resm_idx:]
        # concat strace-logs
        if(pid in un):
            line = pid + " " + time + " " + un[pid] + strace_log
            del un[pid]

    # Finde < > with --decode-fds=all option
    if ('<' in line) and ('>' in line):
        # For '<~~~ (deleted)>' case
        if ('(deleted)' in line):
            line = line.replace(" (deleted)", "[deleted]")

        # replace white space to "_" inside bracket
        bracket_left, bracket_right = check_brackets(line, ['<', '>'])
        for i in range(len(bracket_left)):
            if " " in line[bracket_left[i]:bracket_right[i]]:
                replace_idx = line[bracket_left[i]:bracket_right[i]].find(" ") + bracket_left[i]
                line = line[:replace_idx] + "_" + line[replace_idx + 1:]

    # Find struct
    if ('{st_' in line):
        struct_start = line.index('{st_') + 1
        struct_end = line.rindex('}')
        struct = line[struct_start:struct_end]
        line = line[:struct_start - 1] + "struct" + line[struct_end + 1:]
        #print(line)

    # separate the syscall command and its parameters by spaces
    line = line.replace(", ", ",")
    line = line.translate(str.maketrans({"(": " ", ",": " ", ")": ""}))
    s = line.split(' ')

    # find position of return
    try:
        #ret = s.index('=') + 1
        ret_list = [i for i, value in enumerate(s) if value == '=']
        ret = max(ret_list) + 1
    except ValueError:  # ' = ' is not in list
        continue

    if (s[2] == 'read' or s[2] == 'write'):  # On success, the number of bytes read is returned (zero indicates end of file)
        fd, filename = get_fd_filename(s[3])
        if s[ret] == '?':
            s[ret] = s[ret-2]
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",," + s[ret] + ",," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'pread64' or s[2] == 'pwrite64'):
        fd, filename = get_fd_filename(s[3])
        if s[ret] == '?':
            s[ret] = s[ret-2]
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[6] + "," + s[ret] + ",," + filename
        wf.write(wlines + "\n")

    # returns the resulting offset location as measured in bytes (on error, return -1)
    elif (s[2] == 'lseek') and s[ret] != '-1':
        fd, filename = get_fd_filename(s[3])
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[ret] + ",,," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'openat' or s[2] == 'open' or s[2] == 'creat' or s[2] == 'memfd_create') and s[ret] != '-1':  # on error, return -1
        start = line.find('"')
        end = line.rfind('"')
        filename = '"' + line[start+1:end] + '"'
    
        if '<' in s[ret]:
            fd, linked_file = get_fd_filename(s[ret])

            if linked_file == filename:
                wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,," + filename
            else:
                wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,," + filename[:-1] + "->" + linked_file[1:]
        
        else:
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[ret] + ",,,," + filename
    
        wf.write(wlines + "\n")

    elif (s[2] == 'close') and s[ret] == '0':  # on success
        fd, filename = get_fd_filename(s[3])
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'mmap') and s[ret] != '-1':  # on error, return -1
        if 'MAP_SHARED' in s[6]:
            s[0] = 'MAP_SHARED'
        if s[7] == '-1' and s[8] == '0':
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + '-1' + "," + s[6] + "," + s[4] + "," + s[ret] + ","
        else:
            fd, filename = get_fd_filename(s[7])
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[8]+"|"+s[6] + "," + s[4] + "," + s[ret] + "," + filename
        wf.write(wlines + "\n")

    elif (s[2] == 'munmap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,," + s[4] + "," + s[3]
        wf.write(wlines + "\n")

    elif (s[2] == 'mremap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,," + s[4] + "::" + s[5] + "," + s[3] + "::" + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'brk') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'msync') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,," + s[4] + "," + s[3]
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

            fd, filename = get_fd_filename(s[3])
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,," + filename + ","+ struct[1][7:]   # length of 'st_ino=' == 7
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

    elif (s[2] == 'fork'):
        wlines = s[1] + "," + s[0] + "," + s[2] + "," + s[ret]
        wf.write(wlines + "\n")

    elif (s[2] == 'clone'):
        wlines = s[1] + "," + s[0] + "," + s[2] + "," + s[ret] + ",," + s[4][6:]
        wf.write(wlines + "\n")

    elif (s[2] == 'socket') and s[ret] != '-1':
        fd, socketname = get_fd_filename(s[ret])
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,," + socketname
        wf.write(wlines + "\n")
    
    elif (s[2] == 'socketpair') and s[ret] != '-1':
        fd1, socketname1 = get_fd_filename(s[ret-3][1:])
        fd2, socketname2 = get_fd_filename(s[ret-2][:-1])

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "::" + fd2 + ",,,," + socketname1[:-1] + "::" + socketname2[1:]
        wf.write(wlines + "\n")

    elif (s[2] == 'pipe' or s[2] == 'pipe2') and s[ret] != '-1':
        fd1, pipename1 = get_fd_filename(s[3][1:])
        fd2, pipename2 = get_fd_filename(s[4][:-1])
        
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "::" + fd2 + ",,,," + pipename1[:-1] + "::" + pipename2[1:]
        wf.write(wlines + "\n")

    elif (s[2] == 'dup' or s[2] == 'dup2' or s[2] == 'dup3') and s[ret] != '-1':
        fd1, filename1 = get_fd_filename(s[3])
        fd2, filename2 = get_fd_filename(s[ret])

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "::" + fd2 + ",,,," + filename1[:-1] + "::" + filename2[1:]
        wf.write(wlines + "\n")

    elif (s[2] == 'fcntl') and s[ret] != '-1' and ('F_DUPFD' in s[4]):
        fd1, filename1 = get_fd_filename(s[3])
        fd2, filename2 = get_fd_filename(s[ret])

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "::" + fd2 + "," + s[4] + ",,," + filename1[:-1] + "::" + filename2[1:]
        wf.write(wlines + "\n")

    elif (s[2] == 'eventfd' or s[2] == 'eventfd2') and s[ret] != '-1':
        fd, filename = get_fd_filename(s[ret])
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[3] + ",,," + filename
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
