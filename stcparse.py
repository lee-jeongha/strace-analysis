import argparse

def get_fd_filename(trace_line, start_idx):
    for i in range(start_idx, len(trace_line)):
        idx = trace_line[i].find('>')
        if idx > 0 and (trace_line[i][idx-1] != '-' or trace_line[i][idx-1] != '='):
            end_idx = i
            break
    fd_filename = ''.join(trace_line[start_idx:end_idx+1])

    start = fd_filename.find('<')
    end = fd_filename.rfind('>')

    fd = fd_filename[:start]
    filename = "'" + fd_filename[start+1:end] + "'"
    filename = filename.replace(" ", "_")
    filename = filename.replace('"', '`')

    return str(fd), filename

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

def get_struct(line):
    start_struct_idx = line.find('{st_')
    start_symbol, end_symbol = '{', '}'
    start_idx, end_idx = check_brackets_pair(line=line, start_symbol=start_symbol, end_symbol=end_symbol, offset_idx=start_struct_idx)

    struct = line[start_idx+1:end_idx]
    line = line[:start_idx]+"{struct}"+line[end_idx+1:]

    struct = struct.split('st_')[1:]
    struct = [struct[i].strip(', ') for i in range(len(struct))]
    struct = [struct[i][struct[i].find('=')+1:] for i in range(len(struct))]

    return line, struct

def parse_syscall_line(line):
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

        # put pid(key) with strace-log(value) in 'unfinished_dict'
        unfinished_dict[pid] = strace_log
        return 0

    elif ('resumed>' in line):
        split_line = line.split(sep=' ', maxsplit=2)
        pid = split_line[0]
        time = split_line[1]
        strace_log = split_line[2]

        # length of string 'resumed>' is 8
        resm_idx = strace_log.rfind('resumed>') + 8
        # get pid(key) with the front part of strace-log(value) in 'unfinished_dict'
        strace_log = strace_log[resm_idx:]
        # concat strace-logs
        if (pid in unfinished_dict.keys()):
            line = pid + " " + time + " " + unfinished_dict[pid] + strace_log
            del unfinished_dict[pid]

    # Find struct
    if ('{st_' in line):
        line, struct = get_struct(line=line)

    # Separate the syscall command and its parameters
    if ('(' in line) or (')' in line):
        start_idx, end_idx = check_brackets_pair(line=line, start_symbol='(', end_symbol=')')
        line = list(line)
        line[start_idx] = " ";  line[end_idx] = ""
        line = "".join(line)
    else:
        print("error on :", line)

    # Make list of syscall arguments
    line = line.replace(",", "")
    s = line.split(" ")

    # Find position of return
    try:
        #ret = s.index('=') + 1
        ret_list = [i for i, value in enumerate(s) if value == '=']
        ret = max(ret_list) + 1
    except ValueError:  # ' = ' is not in list
        return 0

    if (s[2] == 'read' or s[2] == 'write'):  # on success, the number of bytes read is returned (zero indicates end of file)
        fd, filename = get_fd_filename(s, 3)
        s[ret] = '0' if s[ret] == '?' else s[ret]
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,," + s[ret] + ",," + filename

    elif (s[2] == 'pread64' or s[2] == 'pwrite64'):
        fd, filename = get_fd_filename(s, 3)
        s[ret] = '0' if s[ret] == '?' else s[ret]
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[ret-2] + ",," + s[ret] + ",," + filename

    elif (s[2] == 'lseek') and s[ret] != '-1':  # returns the resulting offset location as measured in bytes (on error, return -1)
        fd, filename = get_fd_filename(s, 3)
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[ret] + "," + s[ret-2] + "," + s[ret-3] + ",," + filename

    elif (s[2] == 'openat' or s[2] == 'open' or s[2] == 'creat' or s[2] == 'memfd_create') and s[ret] != '-1':  # on error, return -1
        start = line.find('"')
        end = line[(start+1):].find('"') + (start+1)
        filename = "'" + line[start+1:end] + "'"

        for f in s:
            if f.startswith('O_') or f.startswith('MFD_'):  # 'O_' for `open`, `openat` / 'MFD_' for `memfd_create`
                flags = f
            else:
                flgas = ''
    
        if '<' in s[ret]:
            fd, linked_file = get_fd_filename(s, ret)

            if linked_file == filename:
                wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",," + flags + ",,," + filename
            else:
                wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",," + flags + ",,," + filename[:-1] + "=>" + linked_file[1:]
        
        else:
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[ret] + ",," + flags + ",,," + filename

    elif (s[2] == 'close') and s[ret] == '0':  # on success
        fd, filename = get_fd_filename(s, 3)
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,,," + filename

    elif (s[2] == 'mmap') and s[ret] != '-1':  # on error, return -1
        if s[7] == '-1':
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + s[7] + "," + s[8] + ",," + s[4] + "," + s[ret]
        else:
            fd, filename = get_fd_filename(s, 7)
            wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + "," + s[8] + ",," + s[4] + "," + s[ret] + "," + filename

    elif (s[2] == 'munmap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,," + s[4] + "," + s[3]

    elif (s[2] == 'mremap') and s[ret] != '-1':  # on error, return -1
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,," + s[5] + "," + s[3] + "||" + s[ret]

    elif (s[2] == 'stat') and s[ret] != '-1':
        # blank in filename
        start = line.find('"')
        end = line[(start+1):].find('"') + (start+1)
        filename = "'" + line[start+1:end] + "'"

        st_size = struct[8] if not 'makedev(' in struct[8] else 'unknown'
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,," + st_size + ",," + filename + "," + struct[1]
        struct = ''  # flush struct

    elif (s[2] == 'fstat') and s[ret] != '-1':
        fd, filename = get_fd_filename(s, 3)

        st_size = struct[8] if not 'makedev(' in struct[8] else 'unknown'
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,," + st_size + ",," + filename + ","+ struct[1]

        struct = ''  # flush struct

    elif (s[2] == 'lstat') and s[ret] != '-1':
        # blank in filename
        start = line.find('"')
        end = line[(start+1):].find('"') + (start+1)
        filename = "'" + line[start+1:end] + "'"

        st_size = struct[8] if not 'makedev(' in struct[8] else 'unknown'
        wlines = s[1] + "," + s[0] + "," + s[2] + ",,,,," + st_size + ",," + filename + "," + struct[1]
        struct = ''  # flush struct

    elif (s[2] == 'fork'):
        wlines = s[1] + "," + s[0] + "," + s[2] + "," + s[ret]

    elif (s[2] == 'clone'):
        wlines = s[1] + "," + s[0] + "," + s[2] + "," + s[ret] + ",,," + s[4][6:]

    elif (s[2] == 'socket') and s[ret] != '-1':
        fd, socketname = get_fd_filename(s, ret)
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,,,," + socketname
    
    elif (s[2] == 'socketpair') and s[ret] != '-1':
        s[ret-3] = s[ret-3][1:];    s[ret-2] = s[ret-2][:-1]
        fd1, socketname1 = get_fd_filename(s, ret-3)
        fd2, socketname2 = get_fd_filename(s, ret-2)

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "||" + fd2 + ",,,,," + socketname1[:-1] + "||" + socketname2[1:]

    elif (s[2] == 'pipe' or s[2] == 'pipe2') and s[ret] != '-1':
        s[3] = s[3][1:];    s[4] = s[4][:-1]
        fd1, pipename1 = get_fd_filename(s, 3)
        fd2, pipename2 = get_fd_filename(s, 4)
        
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "||" + fd2 + ",,,,," + pipename1[:-1] + "||" + pipename2[1:]

    elif (s[2] == 'dup' or s[2] == 'dup2' or s[2] == 'dup3') and s[ret] != '-1':
        fd1, filename1 = get_fd_filename(s, 3)
        fd2, filename2 = get_fd_filename(s, ret)

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "||" + fd2 + ",,,,," + filename1[:-1] + "||" + filename2[1:]

    elif (s[2] == 'fcntl') and s[ret] != '-1' and ('F_DUPFD' in s[4]):
        fd1, filename1 = get_fd_filename(s, 3)
        fd2, filename2 = get_fd_filename(s, ret)

        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd1 + "||" + fd2 + ",," + s[4] + ",,," + filename1[:-1] + "||" + filename2[1:]

    elif (s[2] == 'eventfd' or s[2] == 'eventfd2') and s[ret] != '-1':
        fd, filename = get_fd_filename(s, ret)
        wlines = s[1] + "," + s[0] + "," + s[2] + ",," + fd + ",,," + s[3] + ",," + filename

    '''
    #elif s[1].startswith('readlink'):	# 433264 readlink("/proc/self/exe", "/usr/bin/python3.8", 4095) = 18
    #  wlines = "89  " + s[2][:-1] + " " + str(int(s[3][:-1], 16)) + " " + s[1][9:-1] + " " + str(int(s[5], 16))

    #elif s[1].startswith('readlinkat'):	# 433264 readlinkat(0x3, "/proc/self/exe", "/usr/bin/python3.8", 4095) = 18
    #  wlines = "267 " + str(int(s[1][11:-2], 16)) + " " + s[3][:-1] + " " + str(int(s[4][:-1], 16)) + " " + s[2][:-1] + " " + str(int(s[6], 16))
    '''
    if 'wlines' not in locals(): # if not wlines:
        return 0
    return wlines

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="strace parser for [read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,memfd_create,close,stat,fstat,lstat,fork,clone,socket,socketpair,pipe,pipe2,dup,dup2,dup3,fcntl,eventfd,eventfd2]",
                                    epilog="strace -a1 -s0 -f -C -tt -v -yy -z -o input.txt [program]")

    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')

    args = parser.parse_args()

    rf = open(args.input, 'r')
    rlines = rf.readlines()
    wf = open(args.output, 'w')

    global unfinished_dict
    unfinished_dict = dict()  # for '<unfinished ...>' log

    for line in rlines:
        line = line.strip("\n")  # remove '\n'

        wlines = parse_syscall_line(line)
        if wlines == 0:
            continue
        wf.write(wlines + "\n")

    rf.close()
    wf.close()