# strace parser

`strace -a1 -s0 -f -C -e trace=read,write,pread64,pwrite64,open,close,lseek,creat,openat,mmap,munmap,mremap -o input.txt [program]`

* sys\_read : read bytes for open file<br>
  `[read, fd, , (return)count]`
* sys\_write : write bytes for open file<br>
  `[write, fd, , (return)count]`
* sys\_open : connect to open file (-1 on error)<br>
  `[open, (return)fd, , , , *filename]`
* sys\_close : disconnect open file (zero on success, -1 on error)<br>
  `[close, fd]`
* sys\_lseek : move position of next read or write<br>
  `[lseek, fd, (return)offset]`
* sys\_mmap : map files or devices into memory<br>
  `[mmap, fd, offset, (return)addr, length]`
* sys\_munmap : unmap files or devices into memory<br>
  `[munmap, , , addr, length]`
* sys\_mremap : remap a virtual memory address<br>
  `[mremap, old_addr, , (return)addr, new_len]`
* sys\_pread64 : read from a file descriptor at a given offset<br>
  `[pread64, fd, offset(position), , (return)count]`
* sys\_pwrite64 : write to a file descriptor at a given offset<br>
  `[pwrite64, fd, offset(position), , (return)count]`
* sys\_creat : creates file and connect to open file (-1 on error)<br>
  `[creat, (return)fd, , , , *pathname]`
* sys\_openat : open a file relative to a directory file descriptor (-1 on error)<br>
  `[openat, (return)fd, , , , *pathname]`
