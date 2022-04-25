# strace parser

`strace -a1 -s0 -f -C -tt -e trace=read,write,pread64,pwrite64,open,close,lseek,creat,openat,mmap,munmap,mremap -o input.txt [program]`

* sys\_read : read bytes for open file<br>
  `[time, pid, read, fd, , (return)count]`
* sys\_write : write bytes for open file<br>
  `[time, pid, write, fd, , (return)count]`
* sys\_open : connect to open file (-1 on error)<br>
  `[time, pid, open, (return)fd, , , , *filename]`
* sys\_close : disconnect open file (zero on success, -1 on error)<br>
  `[time, pid, close, fd]`
* sys\_lseek : move position of next read or write<br>
  `[time, pid, lseek, fd, (return)offset]`
* sys\_mmap : map files or devices into memory<br>
  `[time, pid, mmap, fd, offset, length, (return)addr]`
* sys\_munmap : unmap files or devices into memory<br>
  `[time, pid, munmap, , , length, addr]`
* sys\_mremap : remap a virtual memory address<br>
  `[time, pid, mremap, old_addr, , new_len, (return)addr]`
* sys\_pread64 : read from a file descriptor at a given offset<br>
  `[time, pid, pread64, fd, offset(position), (return)count]`
* sys\_pwrite64 : write to a file descriptor at a given offset<br>
  `[time, pid, pwrite64, fd, offset(position), (return)count]`
* sys\_creat : creates file and connect to open file (-1 on error)<br>
  `[time, pid, creat, (return)fd, , , , *pathname]`
* sys\_openat : open a file relative to a directory file descriptor (-1 on error)<br>
  `[time, pid, openat, (return)fd, , , , *pathname]`
