# strace Analysis

## get strace log
`strace -a1 -s0 -f -C -tt -v -yy -z -e trace=read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,memfd_create,close,stat,fstat,lstat,fork,clone,socket,socketpair,pipe,pipe2,dup,dup2,dup3,fcntl,eventfd,eventfd2 -o input.txt [program]`
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
* memfd_create : create an anonymous file<br>
* close : disconnect open file (zero on success, -1 on error)<br>
* stat : get file status (zero on success, -1 on error)<br>
* fstat : get file status (zero on success, -1 on error)<br>
* lstat : get file status(if path is a symbolic link, then the link itself is stat-ed, not the file that it refers to) (zero on success, -1 on error)<br>
* fork : create a child process<br>
* clone : create a child process<br>
* socket : create an endpoint for communication<br>
* socketpair : create a pair of connected sockets<br>
* pipe/pipe2 : create pipe<br>
* dup/dup2/dup3 : duplicate a file descriptor<br>
* fcntl : manipulate file descriptor<br>
* eventfd/eventfd2 : create a file descriptor for event notification<br>

## 1. Parse strace log file &nbsp;&nbsp; [stcparse.py]
**time** | **pid** | **op** | **cpid** | **fd** | **offset** | **flag** | **length** | **mem\_addr** | **filename** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
time | pid | **read/write** | | fd | | | (return)count | | `<filename>` | |
time | pid | **pread64/pwrite64** | | fd | offset (pos) | | (return)count | | `<filename>` | |
time | pid | **lseek** | | fd | (return)offset | origin | offset | | `<filename>` |
time | pid | **mmap** | | fd | offset | | length | (return)addr | `<filename>` |
time | pid | **munmap** | | | | | length | addr | |
time | pid | **mremap** | | | | | new\_len | old\_addr \|\| (return)new\_addr | |
time | pid | **creat** | | (return)fd | | | | | \*pathname=>`<filename>` |
time | pid | **open** | | (return)fd | | flags | | | \*filename=>`<filename>` |
time | pid | **openat** | | (return)fd | | flags | | | \*pathname=>`<filename>` |
time | pid | **memfd_create** | | (return)fd | | flags | | | \*name =>`<filename>`| |
time | pid | **close** | | fd | | | | | `<filename>` | |
time | pid | **stat** | | | | | st\_size | | \*path | st\_ino |
time | pid | **fstat** | | fd | | | st\_size | | `<filename>` | st\_ino |
time | pid | **lstat** | | | | | st\_size | | \*path | st\_ino |
time | pid | **fork** | (return)c\_pid | | | | | | | |
time | pid | **clone** | (return)c\_pid | | | flags | | | | |
time | pid | **socket** | | (return)fd | | | | | `<socket>` | |
time | pid | **socketpair** | | sp[0] \|\| sp[1] | | | | | `<socket1>`\|\|`<socket2>` | |
time | pid | **pipe/pipe2** | | pipefd[0] \|\| pipefd[1] | | | | | `<pipe1>`\|\|`<pipe2>` | |
time | pid | **dup/dup2/dup3** | | old_fd \|\| (return)fd | | | | | `<filename1>`\|\|`<filename2>` | |
time | pid | **fcntl** | | fd \|\| (return)fd | | flags | | | `<filename1>`\|\|`<filename2>` | |
time | pid | **eventfd/eventfd2** | | (return)fd | | | initval | | `<filename>` | |

## 2. file I/O analysis &nbsp;&nbsp; [/fileio]
&nbsp;&nbsp;1) get filename-inode list<br>
&nbsp;&nbsp;2) assemble parameters for each read/write operation<br>
&nbsp;&nbsp;3) arrange read/write operation per each block<br>
&nbsp;&nbsp;4) plot graph<br>

## execute code with 'run.sh'
`./run.sh [-i <input_log_file>] [-o <output_directory>] [-s <process>] [-f]`

```
Usage:  ./run.sh -i <input> [options]
        -i | --input  %  (set input file name)
        -o | --output  %  (set output directory name)
        -s | --strace  %   (process to use strace)
        -f | --file     (whether analyze file IO or not)
```
### example
`./run.sh -i firefox-v1.txt -o firefox-v1 -f -s "firefox"` <br>
`./run.sh -i mnist-v3.txt -o mnist-v3 -f -s "python3 mnist_cnn.py"` <br>
`./run.sh -i iris-v2.txt -o iris-v2 -f`
