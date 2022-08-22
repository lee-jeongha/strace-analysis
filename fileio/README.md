<br>

# 2. file I/O analysis &nbsp;&nbsp; [/fileio]
### 1) `/fileio/1fileinode.py` : get filename-inode list
**filename** | **inode**
---- | ----
\*filename1 | 9438455
\*filename2 | 8653595
\*filename3 | 556004699277

### 2) `/fileio/2filetrace.py` : assemble parameters for each read/write operation
**time** | **pid** | **op** | **fd** | **offset** | **length** | **inode**
---- | ---- | ---- | ---- | ---- | ---- | ---- 
02:56:35.695250 | 530864 | read | 3 | 0 | 832 | 10487965
02:56:35.695267 | 530864 | pread64 | 3 | 64 | 784 | 10487965
02:56:35.695283 | 530864 | pread64 | 3 | 848 | 32 | 10487965
02:56:35.695298 | 530864 | pread64 | 3 | 880 | 68 | 10487965
02:56:35.695332 | 530864 | pread64 | 3 | 64 | 784 | 10487965

### 3) `/fileio/3filerefblk.py` : arrange read/write operation per each block
**time** | **time_interval** | **pid** | **operation** | **blocknum** | **inode**
---- | ---- | ---- | ---- | ---- | ----
02:56:35.695250 | 0.000000 | 530864 | read | 0 | 10487965
02:56:35.695267 | 0.000017 | 530864 | read | 0 | 10487965
02:56:35.695283 | 0.000033 | 530864 | read | 0 | 10487965
02:56:35.695298 | 0.000048 | 530864 | read | 0 | 10487965
02:56:35.695332 | 0.000082 | 530864 | read | 0 | 10487965
02:56:35.695347 | 0.000097 | 530864 | read | 0 | 10487965

### 4) `/fileio/plot` : plot graph
 * 1refcountperblock.py
 * 2popularity.py
 * 3blkaccess.py