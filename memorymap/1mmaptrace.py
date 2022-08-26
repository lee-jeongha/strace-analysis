import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str,
                    nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str,
                    nargs='?', default='output.txt', help='output file')

args = parser.parse_args()

### 1. objects for trace read/write operations
mem_dict = dict() # {'pid': memForPid}
pid_cpid = dict()   # {'pid': [cpid]}

class memForPid(object):
    def __init__(self, pid):
        self.pid = pid
        self.mmap_info = dict()   # {'start_addr::endaddr': [mapped_time, 'filename']}

    def set_mmap_info(self, addr, filemap_info):
        self.mmap_info[addr] = filemap_info

    def get_mmap_info(self, addr):
        return self.mmap_info[addr]

    def pop_mmap_info(self, addr):
        filemap_info = self.mmap_info.pop(addr)
        return filemap_info
    
    def get_mapped_addr(self):
        return self.mmap_info.keys()

def create_memForPid(addr, filename, pid, time):
    # create memForPid object
    filemap_info = [time, filename]
    try:
        memForPid_block = mem_dict[pid]
    except KeyError:
        memForPid_block = memForPid(pid)
    memForPid_block.set_mmap_info(addr, filemap_info)
    mem_dict[pid] = memForPid_block

def check_map_state(unmap_start_addr, unmap_end_addr, pid):
    unmap_range_info = {}    # {'start_addr::end_addr' : [unmap_start_addr, unmap_end_addr]}

    if pid == 'MAP_SHARED':
        memForPid_block_list = mem_dict.values()
    else:
        memForPid_block_list = (mem_dict[pid], )
    
    for memForPid_block in memForPid_block_list:
        for key in memForPid_block.get_mapped_addr():
            mapped_addr = [int(addrs) for addrs in key.split("::") if addrs != '']
            if (len(mapped_addr)==2) and ((mapped_addr[1] >= unmap_start_addr and mapped_addr[0] <= unmap_end_addr)):
                unmap_addr = sorted(mapped_addr + [unmap_start_addr, unmap_end_addr])[1:-1]
                if unmap_addr[0] == unmap_addr[1]:
                    continue
                else:
                    unmap_range_info[key] = unmap_addr

    if len(unmap_range_info) == 0:
        raise ReferenceError("No matched address found:", [unmap_start_addr, unmap_end_addr])

    return unmap_range_info

def free_mmap(pid, pre_mapped_addr:list, unmap_addr:list, unmap_time):
    memForPid_block = mem_dict[pid]
    filemap_info = memForPid_block.pop_mmap_info(str(pre_mapped_addr[0]) + "::" + str(pre_mapped_addr[1]))
    time = [filemap_info[0], unmap_time]
    filename = filemap_info[1]

    if (unmap_addr[0] == pre_mapped_addr[0]) and (unmap_addr[1] == pre_mapped_addr[1]):
        return time, filename
    elif unmap_addr[0] == pre_mapped_addr[0]:
        memForPid_block.set_mmap_info(str(unmap_addr[1]) + "::" + str(pre_mapped_addr[1]), filemap_info)
    elif unmap_addr[1] == pre_mapped_addr[1]:
        memForPid_block.set_mmap_info(str(pre_mapped_addr[0]) + "::" + str(unmap_addr[0]), filemap_info)
    else:
        memForPid_block.set_mmap_info(str(unmap_addr[1]) + "::" + str(pre_mapped_addr[1]), filemap_info)
        memForPid_block.set_mmap_info(str(pre_mapped_addr[0]) + "::" + str(unmap_addr[0]), filemap_info)
    return time, filename

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


### 3. track syscalls line by line
rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')

for line in rlines:
    line = line.strip("\n")  # remove '\n'

    # separate the syscall log by comma
    s = line.split(',')

    #---
    if s[C_op] == 'mmap':
        if ('MAP_GROWSDOWN' in s[C_offset_flags]) or ('MAP_STACK' in s[C_offset_flags]):
            start_addr = (int(s[C_mem], 16) + int('0x1000', 16)) >> 12
            end_addr = (int(s[C_mem], 16) + int('0x1000', 16) + int(s[C_length])) >> 12
            s[C_filename] = "STACK_mmap"
        else:
            start_addr = int(s[C_mem], 16) >> 12
            end_addr = (int(s[C_mem], 16) + int(s[C_length])) >> 12

        addr = str(start_addr) + "::" + str(end_addr)

        if 'MAP_FIXED' in s[C_offset_flags]:
            try:
                pid_str = "|".join(pid_cpid[s[C_pid]])
                pid_str += "|" + s[C_pid]
            except KeyError:
                pid_str = s[C_pid]
            try:
                unmap_range_info = check_map_state(start_addr, end_addr, s[C_pid])
                for key, value in unmap_range_info.items():
                    pre_mapped_addr = [int(addrs) for addrs in key.split("::")]
                    time, filename = free_mmap(s[C_pid], pre_mapped_addr, unmap_addr=value, unmap_time=s[C_time])
                    wlines = time[0] + "," + time[1] + "," + pid_str + "," + filename + "," + str(value[0]) + "," + str(value[1])
                    wf.write(wlines + "\n")
            except ReferenceError as ke:
                print("MAP_FIXED","|", s[C_time], "|" , end_addr-start_addr, ",", [start_addr, end_addr])

        create_memForPid(addr=addr, filename=s[C_filename].strip('"'), pid=s[C_pid], time=s[C_time])

    elif s[C_op] == 'brk':
        try:
            memForPid_block = mem_dict[s[C_pid]]

            for key, value in memForPid_block.mmap_info.items():
                if 'HEAP_brk' in value[1]:
                    heap_addr = key
                    start_addr = heap_addr.split("::")[0]
                    start_time = value[0]

            memForPid_block.pop_mmap_info(heap_addr)
            end_addr = int(s[C_mem], 16) >> 12
            addr = str(start_addr) + "::" + str(end_addr)
            end_time = s[C_time]

        # first brk for s[C_pid]
        except KeyError as e:
            print(e)
            start_time = s[C_time]
            end_time = s[C_time]

            start_addr = int(s[C_mem], 16) >> 12
            end_addr = ''
            addr = str(start_addr) + "::"

            memForPid_block = memForPid(s[C_pid])

        filemap_info = [s[C_time], "HEAP_brk"]
        memForPid_block.set_mmap_info(addr, filemap_info)
        mem_dict[s[C_pid]] = memForPid_block

        wlines = start_time + "," + end_time + "," + s[C_pid] + "," + "HEAP_brk" + "," + str(start_addr) + "," + str(end_addr)
        wf.write(wlines + "\n")
    
    elif s[C_op] == 'munmap':
        start_addr = int(s[C_mem], 16) >> 12
        if int(s[C_length]) < int('0x1000', 16):
            end_addr = (int(s[C_mem], 16) + int('0x1000', 16)) >> 12
        else:
            end_addr = (int(s[C_mem], 16) + int(s[C_length])) >> 12
        addr = str(start_addr) + "::" + str(end_addr)

        memForPid_block = mem_dict[s[C_pid]]

        try:
            filemap_info = memForPid_block.pop_mmap_info(addr)

            wlines = filemap_info[0] + "," + s[C_time] + "," + s[C_pid] + "," + filemap_info[1] + "," + str(start_addr) + "," + str(end_addr)
            wf.write(wlines + "\n")
        except KeyError as e:
            try:
                pid_str = "|".join(pid_cpid[s[C_pid]])
                pid_str += "|" + s[C_pid]
            except KeyError:
                pid_str = s[C_pid]
            try:
                unmap_range_info = check_map_state(start_addr, end_addr, s[C_pid])
                for key, value in unmap_range_info.items():
                    pre_mapped_addr = [int(addrs) for addrs in key.split("::")]
                    time, filename = free_mmap(s[C_pid], pre_mapped_addr, unmap_addr=value, unmap_time=s[C_time])
                    wlines = time[0] + "," + time[1] + "," + pid_str + "," + filename + "," + str(value[0]) + "," + str(value[1])
                    wf.write(wlines + "\n")
            except ReferenceError as Re:
                print("munmap", "|", s[C_time], "|" , end_addr-start_addr, ",", [start_addr, end_addr])

    elif s[C_op] == 'mremap':
        old_addr = s[C_mem].split("::")[0]
        new_addr = s[C_mem].split("::")[1]
        old_len = s[C_length].split("::")[0]
        new_len = s[C_length].split("::")[1]

        # 1. unmap
        start_addr = int(old_addr, 16) >> 12
        if int(old_len) < int('0x1000', 16):
            end_addr = (int(old_addr, 16) + int('0x1000', 16)) >> 12
        else:
            end_addr = (int(old_addr, 16) + int(old_len)) >> 12
        addr = str(start_addr) + "::" + str(end_addr)

        memForPid_block = mem_dict[s[C_pid]]

        try:
            filemap_info = memForPid_block.pop_mmap_info(addr)
            wlines = filemap_info[0] + "," + s[C_time] + "," + s[C_pid] + "," + filemap_info[1] + "," + str(start_addr) + "," + str(end_addr)
            wf.write(wlines + "\n")
        except KeyError as e:
            try:
                pid_str = "|".join(pid_cpid[s[C_pid]])
                pid_str += "|" + s[C_pid]
            except KeyError:
                pid_str = s[C_pid]
            try:
                unmap_range_info = check_map_state(start_addr, end_addr, s[C_pid])
                for key, value in unmap_range_info.items():
                    pre_mapped_addr = [int(addrs) for addrs in key.split("::")]
                    time, filename = free_mmap(s[C_pid], pre_mapped_addr, unmap_addr=value, unmap_time=s[C_time])
                    wlines = time[0] + "," + time[1] + "," + pid_str + "," + filename + "," + str(value[0]) + "," + str(value[1])
                    wf.write(wlines + "\n")
            except ReferenceError as Re:
                print("mremap", "|", s[C_time], "|" , end_addr-start_addr, ",", [start_addr, end_addr])

        # 2. memory mapping
        start_addr = int(new_addr, 16) >> 12
        end_addr = (int(new_addr, 16) + int(new_len)) >> 12
        addr = str(start_addr) + "::" + str(end_addr)

        if 'MREMAP_FIXED' in s[C_offset_flags]:
            try:
                pid_str = "|".join(pid_cpid[s[C_pid]])
                pid_str += "|" + s[C_pid]
            except KeyError:
                pid_str = s[C_pid]
            try:
                unmap_range_info = check_map_state(start_addr, end_addr, s[C_pid])
                for key, value in unmap_range_info.items():
                    pre_mapped_addr = [int(addrs) for addrs in key.split("::")]
                    time, filename = free_mmap(s[C_pid], pre_mapped_addr, unmap_addr=value, unmap_time=s[C_time])
                    wlines = time[0] + "," + time[1] + "," + pid_str + "," + filename + "," + str(value[0]) + "," + str(value[1])
                    wf.write(wlines + "\n")
            except ReferenceError as ke:
                print("MREMAP_FIXED","|", s[C_time], "|" , end_addr-start_addr, ",", [start_addr, end_addr])

        create_memForPid(addr=addr, filename=s[C_filename].strip('"'), pid=s[C_pid], time=s[C_time])

    elif s[C_op] == 'fork':
        memForPid_block = mem_dict[s[C_pid]]
        c_mmap_info = memForPid_block.mmap_info.copy()
        
        c_memForPid_block = memForPid(s[C_cpid])
        c_memForPid_block.mmap_info = c_mmap_info
        
        mem_dict[s[C_cpid]] = c_memForPid_block
    
    elif s[C_op] == 'clone':
        try:
            memForPid_block = mem_dict[s[C_pid]]
        except KeyError:
            memForPid_block = memForPid(s[C_cpid])

        if 'CLONE_VM' in s[C_offset_flags]:
            c_memForPid_block = memForPid_block   # copy object
            try:
                cpid_list = pid_cpid[s[C_pid]]
                cpid_list.append(s[C_cpid])
                pid_cpid[s[C_pid]] = cpid_list
            except KeyError:
                pid_cpid[s[C_pid]] = [s[C_cpid],]
        else:
            c_mmap_info = memForPid_block.mmap_info.copy()    # deep copy

            c_memForPid_block = memForPid(s[C_cpid])    # create new fdForPid
            c_memForPid_block.mmap_info = c_mmap_info
        
        mem_dict[s[C_cpid]] = c_memForPid_block
    
    current_time = s[C_time]

else:    # No more lines to be read from file
    for pid, memForPid_block in mem_dict.items():
        try:
            pid_str = "|".join(pid_cpid[pid])
            pid_str += "|" + pid
        except KeyError:
            pid_str = pid

        u_mmap_addrs = memForPid_block.mmap_info.copy().keys()
        for key in u_mmap_addrs:
            unmap_addr = [int(addrs) for addrs in key.split("::")]
            try:
                value = memForPid_block.mmap_info[key]
            except:
                print("already unmapped")
                continue
            time, filename = free_mmap(pid, pre_mapped_addr=unmap_addr, unmap_addr=unmap_addr, unmap_time=current_time)
            wlines = time[0] + "," + time[1] + "," + pid_str + "," + filename + "," + str(unmap_addr[0]) + "," + str(unmap_addr[1])
            wf.write(wlines + "\n")

rf.close()
wf.close()

#for pid, memForPid_block in mem_dict.items():
#    print(pid, memForPid_block.mmap_info)
