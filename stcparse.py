import argparse, textwrap
from argparse import RawTextHelpFormatter

#parser = argparse.ArgumentParser(description="strace parser for [read / write / open / close / lseek / mmap / munmap / pread64 / pwirte64 / mremap / creat / openat]")
parser = argparse.ArgumentParser(
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description=textwrap.dedent('''\
	strace parser for [read/write/open/close/lseek/pread64/pwirte64/creat/openat] \n
		sys_read : read bytes for open file
		  [read, fd, , (return)count] \n
		sys_write : write bytes for open file
		  [write, fd, , (return)count] \n
		sys_open : connect to open file (-1 on error)
		  [open, (return)fd, , , , *filename] \n
		sys_close : disconnect open file (zero on success, -1 on error)
		  [close, fd] \n
		sys_lseek : move position of next read or write
		  [lseek, fd, (return)offset] \n
		sys_pread64 : read from a file descriptor at a given offset
		  [pread64, fd, offset(position), , (return)count] \n
		sys_pwrite64 : write to a file descriptor at a given offset
		  [pwrite64, fd, offset(position), , (return)count] \n
		sys_creat : creates file and connect to open file (-1 on error)
		  [creat, (return)fd, , , , *pathname] \n
		sys_openat : open a file relative to a directory file descriptor (-1 on error)
		  [openat, (return)fd, , , , *pathname] \n
		'''),
	epilog="strace -a1 -s0 -f -C -e trace=read,write,pread64,pwrite64,open,close,lseek,creat,openat -o input.txt python3 *.py")

parser.add_argument('input', metavar='I', type=str, nargs='?', default='input.txt',
                    help='input file')
parser.add_argument('output', metavar='O', type=str, nargs='?', default='output.txt',
                    help='output file')

args = parser.parse_args()
#print(args.input, args.output) #, args.infile)


rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')

un = dict() # for '<unfinished ...>' log 

for line in rlines:
  line = line.strip("\n") # remove '\n'
  
  if ('<unfinished' in line):
    pos_end = line.find('<unfinished')  # where a strace log is cut off == where the '<unfinished ...' message is started
    pid_end = line.find(' ')
    # put pid(key) with strace-log(value) in set 'un'
    pid = line[:pid_end]
    strace = line[:pos_end]
    un[pid] = strace
    continue

  elif ('resumed>' in line):
    pos_start = line.rfind('resumed>')+8  # length of string 'resumed>' is 8
    pid_end = line.find(' ')
    # get pid(key) with the front part of strace-log(value) in set 'un'
    pid = line[:pid_end]
    strace = line[pos_start:]
    # concat strace-logs
    if(pid in un):
      line = un[pid] + strace
      #print(line)
      del un[pid]

  # separate the syscall command and its parameters by spaces
  line = line.translate(str.maketrans({ "(":" ", ",":"", ")":"" }))
  s = line.split(' ')
  try:
    ret = s.index('=') + 1
  except ValueError:	# '=' is not in list
    continue
  
  if (s[1]=='read'): #On success, the number of bytes read is returned (zero indicates end of file)
    wlines = s[0] + "," + s[1] + "," + s[2] + ",,," + s[ret]
    wf.write(wlines + "\n")
  
  elif (s[1]=='write'):
    wlines = s[0] + "," + s[1] + "," + s[2] + ",,," + s[ret]
    wf.write(wlines + "\n")
  
  elif (s[1]=='pread64'):
    wlines = s[0] + "," + s[1] + "," + s[2] + "," + s[5] + ",," + s[ret]
    wf.write(wlines + "\n")
  
  elif (s[1]=='pwrite64'):
    wlines = s[0] + "," + s[1] + "," + s[2] + "," + s[5] + ",," + s[ret]
    wf.write(wlines + "\n")
  
  elif (s[1]=='lseek') and s[ret]!='-1':	# returns the resulting offset location as measured in bytes (on error, return -1)
    wlines = s[0] + "," + s[1] + "," + s[2] + "," + s[ret]
    wf.write(wlines + "\n")
  
  elif (s[1]=='openat') and s[ret]!='-1':	# on error, return -1
    wlines = s[0] + "," + s[1] + "," + s[ret] + ",,,," + s[3]
    wf.write(wlines + "\n")
  
  elif (s[1]=='open') and s[ret]!='-1':	# on error, return -1
    wlines = s[0] + "," + s[1] + "," + s[ret] + ",,,," + s[2]
    wf.write(wlines + "\n")
  
  elif (s[1]=='close') and s[ret]=='0':	# on success
    wlines = s[0] + "," + s[1] + "," + s[2]
    wf.write(wlines + "\n")
  
  elif (s[1]=='create') and s[ret]!='-1':	# on error, return -1
    wlines = s[0] + "," + s[1] + "," + s[ret] + ",,,," + s[3]
    wf.write(wlines + "\n")
  
  '''
  #elif s[1].startswith('readlink'):	# 433264 readlink("/proc/self/exe", "/usr/bin/python3.8", 4095) = 18
  #  wlines = "89  " + s[2][:-1] + " " + str(int(s[3][:-1], 16)) + " " + s[1][9:-1] + " " + str(int(s[5], 16))
  #  wf.write(wlines + "\n")
  
  #elif s[1].startswith('readlinkat'):	# 433264 readlinkat(0x3, "/proc/self/exe", "/usr/bin/python3.8", 4095) = 18
  #  wlines = "267 " + str(int(s[1][11:-2], 16)) + " " + s[3][:-1] + " " + str(int(s[4][:-1], 16)) + " " + s[2][:-1] + " " + str(int(s[6], 16))
  #  wf.write(wlines + "\n")
  '''

rf.close()
wf.close()

