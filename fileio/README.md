<br>

# 2. file I/O analysis &nbsp;&nbsp; [/fileio]
### 1) `/fileio/1fileinode.py` : get filename-inode list
**filename** | **inode**
---- | ----
\*filename1 | 169103596144
\*filename2 | 560396772133
\*filename3 | 116957545747

### 2) `/fileio/2filetrace.py` : assemble parameters for each read/write operation
**time** | **pid** | **ppid** | **op** | **fd** | **offset** | **length** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- | ----
17:29:47.800031 | 18234 | 18234 | read | 3 | 0 | 832 | 169103596144
17:29:47.800047 | 18234 | 18234 | pread64 | 3 | 824 | 68 | 169103596144
17:29:47.800088 | 18234 | 18234 | pread64 | 3 | 824 | 68 | 169103596144
17:29:47.800243 | 18234 | 18234 | read | 3 | 0 | 832 | 560396772133
17:29:47.800733 | 18234 | 18234 | read | 3 | 0 | 832 | 342931731962

### 3) `/fileio/3filerefblk.py` : arrange read/write operation per each block
**time** | **pid** | **operation** | **blocknum** | **inode**
---- | ---- | ---- | ---- | ----
0.0 | 18234 | read | 0 | 116957545747
0.0 | 18234 | read | 1 | 116957545747
1.599999814061448e-05 | 18234 | read | 0 | 116957545747 
1.599999814061448e-05 | 18234 | read | 1 | 116957545747 
2.9999995604157448e-05 | 18234 | read | 1 | 116957545747 
4.400000034365803e-05 | 18234 | read | 1 | 116957545747 

### 4) `/fileio/plot` : plot graph
 * 1refcountperblock.py
 * 2popularity.py
 * 3blkaccess.py