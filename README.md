# strace parser

## get strace log
`strace -a1 -s0 -f -C -tt -e trace=read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,close,stat,fstat,lstat,fork,clone -o input.txt [program]`
* sys\_read : read bytes for open file<br>
* sys\_write : write bytes for open file<br>
* sys\_pread64 : read from a file descriptor at a given offset<br>
* sys\_pwrite64 : write to a file descriptor at a given offset<br>
* sys\_lseek : move position of next read or write<br>
* sys\_mmap : map files or devices into memory<br>
* sys\_munmap : unmap files or devices into memory<br>
* sys\_mremap : remap a virtual memory address<br>
* sys\_creat : creates file and connect to open file (-1 on error)<br>
* sys\_open : connect to open file (-1 on error)<br>
* sys\_openat : open a file relative to a directory file descriptor (-1 on error)<br>
* sys\_close : disconnect open file (zero on success, -1 on error)<br>
* sys\_stat : get file status (zero on success, -1 on error)<br>
* sys\_fstat : get file status (zero on success, -1 on error)<br>
* sys\_lstat : get file status(if path is a symbolic link, then the link itself is stat-ed, not the file that it refers to) (zero on success, -1 on error)<br>
* sys\_fork : creat a child process<br>
* sys\_clone : creat a child process<br>

## 1. stcparse.py
**time** | **pid** | **op** | **cpid** | **fd** | **offset** | **length** | **mem\_addr** | **filename** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
time | pid | **read** | | fd | | (return)count | | | |
time | pid | **write** | | fd | | (return)count | | | |
time | pid | **pread64** | | fd | offset (pos) | (return)count | | | |
time | pid | **pwrite64** | | fd | offset (pos) | (return)count | | | |
time | pid | **lseek** | | fd | (return)offset | | | |
time | pid | **mmap** | | fd | offset | length | (return)addr | |
time | pid | **munmap** | | | | length | addr | |
time | pid | **mremap** | | old\_addr | | new\_len | (return)new\_addr | |
time | pid | **creat** | | (return)fd | | | | \*pathname |
time | pid | **open** | | (return)fd | | | | \*filename |
time | pid | **openat** | | (return)fd | | | | \*pathname |
time | pid | **close** | | fd | | | | | |
time | pid | **stat** | | | | | | \*path | st\_ino |
time | pid | **fstat** | | fd | | | | | st\_ino |
time | pid | **lstat** | | | | | | \*path | st\_ino |
time | pid | **fork** | (return)c\_pid | | | | | | |
time | pid | **clone** | (return)c\_pid | | | | | | |

## 2. fileinode.py
**filename** | **inode**
---- | ----
filename1 | inode1
filename2 | inode2
filename3 | inode3

## 3. filetrace.py
**time** | **pid** | **ppid** | **op** | **fd** | **offset** | **length** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
17:29:47.800031 | 18234 | 18234 | read | 3 | 0 | 832 | 169103596144
17:29:47.800047 | 18234 | 18234 | pread64 | 3 | 824 | 68 | 169103596144
17:29:47.800088 | 18234 | 18234 | pread64 | 3 | 824 | 68 | 169103596144
17:29:47.800243 | 18234 | 18234 | read | 3 | 0 | 832 | 560396772133
17:29:47.800733 | 18234 | 18234 | read | 3 | 0 | 832 | 342931731962

## 4. filerefblk.py
**time** | **pid** | **operation** | **blocknum** | **inode** | **read\_blk** | **write\_blk**
---- | ---- | ---- | ---- | ---- | ---- | ----
0.0 | 18234 | read | 0 | 116957545747 | 0 | 
0.0 | 18234 | read | 1 | 116957545747 | 1 | 
1.599999814061448e-05 | 18234 | read | 0 | 116957545747 | 0 | 
1.599999814061448e-05 | 18234 | read | 1 | 116957545747 | 1 | 
2.9999995604157448e-05 | 18234 | read | 1 | 116957545747 | 1 | 
4.400000034365803e-05 | 18234 | read | 1 | 116957545747 | 1 | 

## execute code with 'run.sh'
`./run.sh [-i <input_log_file>] [-o <output_directory>] [-r]`

```
Usage:  ./run.sh -i <input> [options]
        -i | --input  %  (set input file name)
        -o | --output  %  (set output directory name)
        -r | --random_inode     (assign random inode)
```
