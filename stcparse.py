import argparse, textwrap
from argparse import RawTextHelpFormatter

#parser = argparse.ArgumentParser(description="strace parser for [read / write / open / close / lseek / pread64 / pwirte64 / creat / openat]")
parser = argparse.ArgumentParser(
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description=textwrap.dedent('''\
	strace parser for [read/write/open/close/lseek/pread64/pwirte64/creat/openat] \n
		sys_read : read bytes for open file
		  [0, fd, *buf, , count, (return)count] \n
		sys_write : write bytes for open file
		  [1, fd, *buf, , count, (return)count] \n
		sys_open : connect to open file (-1 on error)
		  [2, (return)fd, , , , , *filename] \n
		sys_close : disconnect open file (zero on success, -1 on error)
		  [3, fd] \n
		sys_lseek : move position of next read or write
		  [8, fd, , (return)offset]
		sys_pread64 : read from a file descriptor at a given offset
		  [17, fd, *buf, offset(position), count, (return)count] \n
		sys_pwrite64 : write to a file descriptor at a given offset
		  [18, fd, *buf, offset(position), count, (return)count] \n
		sys_creat : creates file and connect to open file (-1 on error)
		  [85, (return)fd, , , , , *pathname] \n
		sys_openat : open a file relative to a directory file descriptor (-1 on error)
		  [257, (return)fd, , , , , *pathname] \n
		'''),
	epilog="strace -a1 -f -C -e trace=read,write,pread64,pwrite64,open,close,lseek,creat,openat -e raw=read,write,pread64,pwrite64 -o input.txt python3 *.py")

parser.add_argument('input', metavar='I', type=str, nargs='?', default='input.txt',
                    help='input file')
parser.add_argument('output', metavar='O', type=str, nargs='?', default='output.txt',
                    help='output file')

args = parser.parse_args()
#print(args.input, args.output) #, args.infile)


rf = open(args.input, 'r')
rlines = rf.readlines()
wf = open(args.output, 'w')


for line in rlines:
  s = line[:-1].split(' ') # remove '\n'
  try:
    ret = s.index('=') + 1
    sb = s[1].index('(') #start bracket
    #eb = s[ret-1].index(')') #end bracket
  except ValueError:	# '=' is not in list
    continue
  
  if s[1].startswith('read'): #On success, the number of bytes read is returned (zero indicates end of file)
    #wlines = "0," + str(int(s[1][5:-1], 16)) + "," + s[2] + str(int(s[3][:-1], 16)) + ",," + str(int(s[ret], 16))
    wlines = "0," + str(int(s[1][(sb+1):-1], 16)) + "," + s[2][:-1] + ",," + str(int(s[3][:-1], 16)) + "," + str(int(s[ret], 16))
    wf.write(wlines + "\n")
  
  elif s[1].startswith('write'):
    #wlines = "1," + str(int(s[1][6:-1], 16)) + "," + s[2] + str(int(s[3][:-1], 16)) + ",," + str(int(s[ret], 16))
    wlines = "1," + str(int(s[1][(sb+1):-1], 16)) + "," + s[2][:-1] + ",," + str(int(s[3][:-1], 16)) + "," + str(int(s[ret], 16))
    wf.write(wlines + "\n")
  
  elif s[1].startswith('pread64'):
    #wlines = "17," + str(int(s[1][8:-1], 16)) + "," + s[2] + str(int(s[3][:-1], 16)) + "," + str(int(s[4][:-1], 16)) + "," + str(int(s[6], 16))
    wlines = "17," + str(int(s[1][(sb+1):-1], 16)) + "," + s[2][:-1] + "," + s[4][:-1] + "," + str(int(s[3][:-1], 16)) + "," + str(int(s[ret], 16))
    wf.write(wlines + "\n")
  
  elif s[1].startswith('pwrite64'):
    #wlines = "18," + str(int(s[1][9:-1], 16)) + "," + s[2] + str(int(s[3][:-1], 16)) + "," + str(int(s[4][:-1], 16)) + "," + str(int(s[6], 16))
    wlines = "18," + str(int(s[1][(sb+1):-1], 16)) + "," + s[2][:-1] + "," + s[4][:-1] + "," + str(int(s[3][:-1], 16)) + "," + str(int(s[ret], 16))
    wf.write(wlines + "\n")
  
  elif s[1].startswith('lseek'):	# returns the resulting offset location as measured in bytes
    if int(s[ret]) != -1:	# not error
      wlines = "8," + s[1][sb+1:-1] + ",," + s[ret]
      wf.write(wlines + "\n")
  
  elif s[1].startswith('openat'):
    if int(s[ret]) != -1:	# not error
      wlines = "257," + s[ret] + ",,,,," + s[2][:-1]
      wf.write(wlines + "\n")
  
  elif s[1].startswith('open'):
    if int(s[ret]) != -1:	# not error
      wlines = "2," + s[ret] + ",,,,," + s[1][(sb+1):-1]
      wf.write(wlines + "\n")
  
  elif s[1].startswith('close'):
    if int(s[ret]) == 0:	# on success
      wlines = "3," + s[1][(sb+1):-1]
      wf.write(wlines + "\n")
  
  elif s[1].startswith('create'):
    if int(s[ret]) != -1:	# not error
      wlines = "85," + s[ret] + ",,,,," + s[2][(sb+1):-1]
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

