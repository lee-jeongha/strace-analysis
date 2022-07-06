# strace Analysis

## get strace log
`strace -a1 -s0 -f -C -tt -v -e trace=read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,close,stat,fstat,lstat,fork,clone -o input.txt [program]`
* read : read bytes for open file<br>
* write : write bytes for open file<br>
* pread64 : read from a file descriptor at a given offset<br>
* pwrite64 : write to a file descriptor at a given offset<br>
* lseek : move position of next read or write<br>
* mmap : map files or devices into memory<br>
* munmap : unmap files or devices into memory<br>
* mremap : remap a virtual memory address<br>
* creat : creates file and connect to open file (-1 on error)<br>
* open : connect to open file (-1 on error)<br>
* openat : open a file relative to a directory file descriptor (-1 on error)<br>
* close : disconnect open file (zero on success, -1 on error)<br>
* stat : get file status (zero on success, -1 on error)<br>
* fstat : get file status (zero on success, -1 on error)<br>
* lstat : get file status(if path is a symbolic link, then the link itself is stat-ed, not the file that it refers to) (zero on success, -1 on error)<br>
* fork : creat a child process<br>
* clone : creat a child process<br>

## 1. Parse strace log file &nbsp;&nbsp; [./stcparse.py]
**time** | **pid** | **op** | **cpid** | **fd** | **offset** | **length** | **mem\_addr** | **filename** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
time | pid | **read** | | fd | | (return)count | | | |
time | pid | **write** | | fd | | (return)count | | | |
time | pid | **pread64** | | fd | offset (pos) | (return)count | | | |
time | pid | **pwrite64** | | fd | offset (pos) | (return)count | | | |
time | pid | **lseek** | | fd | (return)offset | | | |
time | pid | **mmap** | | fd | offset | length | (return)addr | |
time | pid | **munmap** | | | | length | addr | |
time | pid | **mremap** | | | | new\_len | old\_addr : (return)new\_addr | |
time | pid | **creat** | | (return)fd | | | | \*pathname |
time | pid | **open** | | (return)fd | | | | \*filename |
time | pid | **openat** | | (return)fd | | | | \*pathname |
time | pid | **close** | | fd | | | | | |
time | pid | **stat** | | | | | | \*path | st\_ino |
time | pid | **fstat** | | fd | | | | | st\_ino |
time | pid | **lstat** | | | | | | \*path | st\_ino |
time | pid | **fork** | (return)c\_pid | | | | | | |
time | pid | **clone** | (return)c\_pid | | | | | | |

## 2. file I/O analysis &nbsp;&nbsp; [./fileio]
### 2-1) get filename-inode list -> [./fileio/1fileinode.py]
**filename** | **inode**
---- | ----
\*filename1 | 169103596144
\*filename2 | 560396772133
\*filename3 | 116957545747

### 2-2) assemble parameters for each read/write operation -> [./fileio/2filetrace.py]
**time** | **pid** | **ppid** | **op** | **fd** | **offset** | **length** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
17:29:47.800031 | 18234 | 18234 | read | 3 | 0 | 832 | 169103596144
17:29:47.800047 | 18234 | 18234 | pread64 | 3 | 824 | 68 | 169103596144
17:29:47.800088 | 18234 | 18234 | pread64 | 3 | 824 | 68 | 169103596144
17:29:47.800243 | 18234 | 18234 | read | 3 | 0 | 832 | 560396772133
17:29:47.800733 | 18234 | 18234 | read | 3 | 0 | 832 | 342931731962

### 2-3) arrange read/write operation per each block -> [./fileio/3filerefblk.py]
**time** | **pid** | **operation** | **blocknum** | **inode**
---- | ---- | ---- | ---- | ----
0.0 | 18234 | read | 0 | 116957545747
0.0 | 18234 | read | 1 | 116957545747
1.599999814061448e-05 | 18234 | read | 0 | 116957545747 
1.599999814061448e-05 | 18234 | read | 1 | 116957545747 
2.9999995604157448e-05 | 18234 | read | 1 | 116957545747 
4.400000034365803e-05 | 18234 | read | 1 | 116957545747 

### 2-4) plot graph -> [./fileio/plot]
 * 1refcountperblock.py
 * 2popularity.py
 * 3blkaccess.py

## execute code with 'run.sh'
`./run.sh [-i <input_log_file>] [-o <output_directory>] [-s <process>] [-f] [-r]`

```
Usage:  ./run.sh -i <input> [options]
        -i | --input  %  (set input file name)
        -o | --output  %  (set output directory name)
        -s | --strace  %   (process to use strace)
        -f | --file     (whether analyze file IO or not)
        -r | --random_inode     (whether assign random inode or not)
```
### example
`./run.sh -i firefox-v1.txt -o firefox-v1 -f -r -s "firefox"` <br>
`./run.sh -i mnist-v3.txt -o mnist-v3 -f -r -s "python3 mnist_cnn.py"` <br>
`./run.sh -i iris-v2.txt -o iris-v2 -f -r`
