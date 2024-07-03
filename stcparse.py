import argparse

def check_pair_of_brackets(line):
    b_stack = []  # Stack for checking pair of brackets
    re = []       # List for return value
    partition_idx, b_count = 0, 0

    # Brackets dictionary
    brackets = {')': '(', '}': '{', ']': '[', '>': '<'}

    for i, char in enumerate(line):
        if char in brackets.values():
            # If open bracket
            if not b_stack:
                re.append(line[partition_idx : i])
                partition_idx = i
            b_stack.append((char, i))
            b_count += 1

        elif char in brackets.keys():
            # If closing bracket
            if line[i-1:i+1] == '->' or line[i-1:i+1] == '=>':
                continue
            try:
                p = b_stack.pop()
            except IndexError: # `IndexError: pop from empty list`
                return (False, None)

            if brackets[char] != p[0]:
                # Mismatched
                return (False, None)

            elif not b_stack:
                # Nothing in `b_stack` -> not subset
                re.append(line[p[1] : i+1])
                partition_idx = i+1

            else:
                # subset
                pass
        else:
            # Ignore characters other than brackets
            continue

    if partition_idx < len(line):
        re.append(line[partition_idx:])

    if b_count == 0:
        # Have no brackets
        return (False, re)

    # Remove unnecessary strings
    re = [r for r in re if ((r != ',') and (r != ', ') and (r != ''))]

    return (True, re)

def find_ret(line_list: list):
    # Find position of return
    try:
        for i, value in enumerate(reversed(line_list)):
            if ' = ' in value:
                return (len(line_list) - 1) - i
    except ValueError:  # ' = ' is not in list
        return -1

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

    pid, time, syscall = line.split(maxsplit=2)
    is_syscall, syscall_list = check_pair_of_brackets(syscall)
    if not is_syscall:
        # There is no brackets: '+++ exited with 0 +++'
        return -1

    # Find position of return
    ret_idx = find_ret(syscall_list)
    try:
        assert ret_idx == 2
    except AssertionError:
        return -1
    syscall_list[ret_idx] = syscall_list[ret_idx].lstrip(' = ')

    # (function_name, argumnets, return_value, addtionally_returned)
    syscall_func = syscall_list[0]
    syscall_arguments = syscall_list[1]
    syscall_returns = syscall_list[ret_idx]
    syscall_ret_supplement = None
    if ret_idx < len(syscall_list) - 1: # `prctl()`
        syscall_ret_supplement = syscall_list[ret_idx + 1:]

    if (syscall_func == 'read' or syscall_func == 'write'):  # on success, the number of bytes read is returned (zero indicates end of file)
        syscall_returns = '0' if syscall_returns == '?' else syscall_returns

        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd, _filename = s[0], s[1]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + ",,," + syscall_returns + ",," + _filename[1:-1]

    elif (syscall_func == 'pread64' or syscall_func == 'pwrite64'):
        syscall_returns = '0' if syscall_returns == '?' else syscall_returns
        
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd, _filename = s[0], s[1]
        sysc_args = s[-1].split(', ')

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + "," + sysc_args[-1] + ",," + syscall_returns + ",," + _filename[1:-1]

    elif (syscall_func == 'readv' or syscall_func == 'writev') and syscall_returns != '-1':
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd, _filename = s[0], s[1]

        #iovcnt = s[3].removeprefix(', ')
        #_, iovec = check_pair_of_brackets(s[2][1:-1])
        #iovec = [iov[1:-1].split(', ') for iov in iovec]
        #iovec_len = sum([int(iov[1].split('=')[1]) for iov in iovec])

        wlines = time + "," + pid + "," + syscall_func[:-1] + ",," + fd + ",,," + syscall_returns + ",," + _filename[1:-1]

    elif (syscall_func == 'lseek') and syscall_returns != '-1':  # returns the resulting offset location as measured in bytes (on error, return -1)
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd, _filename = s[0], s[1]
        sysc_args = s[-1].split(', ')

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + "," + syscall_returns + "," + sysc_args[-1] + "," + sysc_args[-2] + ",," + _filename[1:-1]

    elif (syscall_func == 'open' or syscall_func == 'creat' or syscall_func == 'memfd_create') and syscall_returns != '-1':  # on error, return -1
        s = syscall_arguments[1:-1].split(', ')
        fd = syscall_returns
        _filename = s[0]
        filename = _filename[1:-1]

        if s[1].startswith('O_') or s[1].startswith('MFD_'):  # 'O_' for `open` / 'MFD_' for `memfd_create`
            flags = s[1]
            # if ('O_CREAT' in s[1]): mode = s[-1]
        elif s[1].startswith('S_'):
            mode = s[1]

        if syscall_ret_supplement:
            linked_file = syscall_ret_supplement[0]

            if linked_file[1:-1] != filename:
                filename = filename + "=>" + linked_file[1:-1]

        wlines = time + "," + pid + "," + syscall_func + ",," + syscall_returns + ",," + flags + ",,," + filename

    elif (syscall_func == 'openat') and syscall_returns != '-1':  # on error, return -1
        s = syscall_arguments[1:-1].split(', ')
        fd = syscall_returns

        _filename = s[1]
        filename = _filename[1:-1]
        flags = s[2]
        # if ('O_CREAT' in s[2]): mode = s[-1]

        if syscall_ret_supplement:
            linked_file = syscall_ret_supplement[0]

            if linked_file[1:-1] != filename:
                filename = filename + "=>" + linked_file[1:-1]

        wlines = time + "," + pid + "," + syscall_func + ",," + syscall_returns + ",," + flags + ",,," + filename

    elif (syscall_func == 'close') and syscall_returns == '0':  # on success
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd, _filename = s[0], s[1]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + ",,,,," + _filename[1:-1]

    elif (syscall_func == 'mmap') and syscall_returns != '-1':  # on error, return -1
        s = syscall_arguments[1:-1].split(', ')
        _fd = s[-2]
        if _fd == '-1':
            fd, filename = _fd, ''
        else:
            _, sysc_args = check_pair_of_brackets(_fd)
            fd, filename = sysc_args[0], sysc_args[1][1:-1]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + "," + s[-1] + ",," + s[1] + "," + syscall_returns + "," + filename

    elif (syscall_func == 'munmap') and syscall_returns != '-1':  # on error, return -1
        s = syscall_arguments[1:-1].split(', ')
        wlines = time + "," + pid + "," + syscall_func + ",,,,," + s[1] + "," + s[0]

    elif (syscall_func == 'mremap') and syscall_returns != '-1':  # on error, return -1
        s = syscall_arguments[1:-1].split(', ')
        wlines = time + "," + pid + "," + syscall_func + ",,,,," + s[2] + "," + s[0] + "||" + syscall_returns

    elif (syscall_func == 'stat' or syscall_func == 'lstat') and syscall_returns != '-1':
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        _filename, struct_string = s[0], s[1]

        filename = _filename.strip(', ')[1:-1]

        struct = struct_string[1:-1].split('st_')
        struct = [st.strip(', ') for st in struct if st != '']
        st_ino = struct[1].split('=')[1]

        wlines = time + "," + pid + "," + syscall_func + ",,,,," + st_size + ",," + filename + "," + st_ino

    elif (syscall_func == 'fstat') and syscall_returns != '-1':
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd, _filename, struct_string = s[0], s[1], s[2]
        
        struct = struct_string[1:-1].split('st_')
        struct = [st.strip(', ') for st in struct if st != '']

        st_ino = struct[1].split('=')[1]
        st_size = 'unknown'
        for st in struct:
            if st.startswith('size='):
                st_size = st.split('=')[1]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + ",,," + st_size + ",," + _filename[1:-1] + ","+ st_ino

    elif (syscall_func == 'fork'):
        wlines = time + "," + pid + "," + syscall_func + "," + syscall_returns

    elif (syscall_func == 'clone'):
        s = syscall_arguments[1:-1].split(', ')
        _flags = s[1]
        wlines = time + "," + pid + "," + syscall_func + "," + syscall_returns + ",,," + _flags.split('=')[1]

    elif (syscall_func == 'socket') and syscall_returns != '-1':
        fd, _socketname = syscall_returns, syscall_ret_supplement[0]
        wlines = time + "," + pid + "," + syscall_func + ",," + fd + ",,,,," + _socketname[1:-1]

    elif (syscall_func == 'socketpair') and syscall_returns != '-1':
        sysc_args = syscall_arguments[1:-1].split(', ', 3)
        _, sysc_args = check_pair_of_brackets(sysc_args[3][1:-1])
        sysc_args = [a.strip(', ') for a in sysc_args]

        fd1, _socketname1 = sysc_args[0], sysc_args[1]
        fd2, _socketname2 = sysc_args[2], sysc_args[3]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd1 + "||" + fd2 + ",,,,," + _socketname1[1:-1] + "||" + _socketname2[1:-1]

    elif (syscall_func == 'pipe' or syscall_func == 'pipe2') and syscall_returns != '-1':
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        pipes = s[0]
        _, pipes = check_pair_of_brackets(pipes[1:-1])
        pipes = [a.strip(', ') for a in pipes]

        fd1, _pipename1 = pipes[0], pipes[1]
        fd2, _pipename2 = pipes[2], pipes[3]
        
        wlines = time + "," + pid + "," + syscall_func + ",," + fd1 + "||" + fd2 + ",,,,," + _pipename1[1:-1] + "||" + _pipename2[1:-1]

    elif (syscall_func == 'dup' or syscall_func == 'dup2' or syscall_func == 'dup3') and syscall_returns != '-1':
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])
        fd1, _filename1 = s[0], s[1]
        fd2, _filename2 = syscall_returns, syscall_ret_supplement[0]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd1 + "||" + fd2 + ",,,,," + _filename1[1:-1] + "||" + _filename2[1:-1]

    elif (syscall_func == 'fcntl') and syscall_returns != '-1':
        _, s = check_pair_of_brackets(syscall_arguments[1:-1])

        if not ('F_DUPFD' in s[2]):
            return 0
        flags = s[2].removeprefix(', ').replace(', ', '|')

        fd1, _filename1 = s[0], s[1]
        fd2, _filename2 = syscall_returns, syscall_ret_supplement[0]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd1 + "||" + fd2 + ",," + flags + ",,," + _filename1[1:-1] + "||" + _filename2[1:-1]

    elif (syscall_func == 'eventfd' or syscall_func == 'eventfd2') and syscall_returns != '-1':
        fd, _filename = syscall_returns, syscall_ret_supplement[0]
        interval = syscall_arguments[1:-1].split(', ')[0]

        wlines = time + "," + pid + "," + syscall_func + ",," + fd + ",,," + interval + ",," + _filename[1:-1]

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
        elif wlines == -1:
            print("error on :", line)
            continue
        wf.write(wlines + "\n")

    rf.close()
    wf.close()
