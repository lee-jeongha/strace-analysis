strace parser for syscalls

`strace -a1 -s0 -f -C -e trace=read,write,pread64,pwrite64,open,close,lseek,creat,openat,mmap,munmap,mremap -o input.txt python3 \*.py`

* sys\_read : read bytes for open file
  [read, fd, , (return)count]
* sys\_write : write bytes for open file
  [write, fd, , (return)count]
* sys\_open : connect to open file (-1 on error)
  [open, (return)fd, , , , \*filename]
* sys\_close : disconnect open file (zero on success, -1 on error)
  [close, fd]
* sys\_lseek : move position of next read or write
  [lseek, fd, (return)offset]
* sys\_mmap : map files or devices into memory
  [mmap, fd, offset, (return)addr, length] \n
* sys\_munmap : unmap files or devices into memory
  [munmap, , , addr, length]
* sys\_mremap : remap a virtual memory address
  [mremap, old\_addr, , (return)addr, new\_len]
* sys\_pread64 : read from a file descriptor at a given offset
  [pread64, fd, offset(position), , (return)count]
* sys\_pwrite64 : write to a file descriptor at a given offset
  [pwrite64, fd, offset(position), , (return)count]
* sys\_creat : creates file and connect to open file (-1 on error)
  [creat, (return)fd, , , , \*pathname]
* sys\_openat : open a file relative to a directory file descriptor (-1 on error)
  [openat, (return)fd, , , , \*pathname]
