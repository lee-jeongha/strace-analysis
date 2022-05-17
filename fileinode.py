import argparse
import csv
import os
import subprocess   # to get cmd results
import string, random

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt', help='output file')
parser.add_argument("--random_inode", action='store_true', help="[get inode from fstat / assign unique number to each file]")

args = parser.parse_args()

#----

fd_inode = dict() # {'pid,fd':'filename'}, for on-line tracking
file_inode = dict() # {'filename':inode}, for saving
ppid = dict()   # save parent pid

def random_str(length):
  string_pool = string.digits # 0~9
  result = ''
  for i in range(length):
    result += random.choice(string_pool) # get random number
  return result

#----
### get inode from fstat ###
if (not args.random_inode):
  with open(args.input) as rf:
      reader=csv.reader(rf, delimiter=',')
    
      for i, line in enumerate(reader):
        #print(line)
        if (line[2]=='open') or (line[2]=='openat') or (line[2]=='creat'):
          fd_inode[line[1]+","+line[4]] = line[8]  # line[1]:pid, line[4]:fd
          #print(fd_inode)
      
        elif (line[2]=='fork') or(line[2]=='clone'):
          ppid[line[3]] = line[1] # {'pid':'ppid'}

        elif (line[2]=='fstat'):
          if line[4]=='0' or line[4]=='1' or line[4]=='2':  # stdinput, stdoutput, stderror
            continue
          try:
            filename = fd_inode.pop(line[1]+","+line[4])  # line[1]:pid, line[4]:fd
            if (not (filename in file_inode.keys())) or (filename.find('manually') != -1):
              file_inode[filename] = line[9]    # line[9]:inode
          except KeyError:  # try to get inode of closed file state or already done 'fstat'
            try: # fstat on parent fd
              parent = ppid[line[1]]
              filename = fd_inode.pop(parent+","+line[4])
              if not filename in file_inode.keys():
                file_inode[filename]=line[9]
            except KeyError: # not child process
              continue
      
        elif (line[2]=='stat') or (line[2]=='lstat'):
          if not line[8] in file_inode.keys():
            file_inode[line[8]] = line[9] # line[8]:filename, line[9]:inode

        elif (line[2]=='close'):
          try:
            # close file without running 'fstat'
            filename = fd_inode.pop(line[1]+","+line[4])  # line[1]:pid, line[4]:fd
            # find inode manually
            if (not (filename in file_inode.keys())) or (filename.find('manually') != -1):
              stat_cmd = "stat "+filename+" | grep Inode | awk '{print $4}'"
              inode = str(subprocess.getstatusoutput("LANG=C"+stat_cmd)[1])  # str(os.system(stat_cmd))
              file_inode[filename] = inode+'-manually_found'
              print('"'+filename+'",'+inode+'-manually_found\n')
          except KeyError:  # done fstat already
            continue

  # files without running 'close'
  for pid_fd, filenames in fd_inode.items():
      if not (filenames in file_inode):
        stat_cmd = "stat "+filenames+" | grep Inode | awk '{print $4}'"
        inode = str(subprocess.getstatusoutput("LANG=C"+stat_cmd)[1])  # str(os.system(stat_cmd))
        file_inode[filenames] = inode+'-manually_found-unclosed'
        print('"'+filenames+'",'+inode+'-manually_found-unclosed\n')

  # save file-inode list
  wf = open(args.output, 'w')

  for filenames, inodes in file_inode.items():
      # "stat: cannot stat '...': no such file or directory" ":Permission denied" message
    if inodes.find(':') != -1:
      inodes = random_str(10)+"-random_number"
    # save
    wf.write('"'+filenames+'",'+inodes+'\n')

  wf.close()

#----
### assign unique number to each file ###
else:
  with open(args.input) as rf:
      reader=csv.reader(rf, delimiter=',')
  
      for i, line in enumerate(reader):
        #print(line)
        if (line[2]=='open') or (line[2]=='openat') or (line[2]=='creat'):
          fd_inode[line[1]+","+line[4]] = line[8]  # line[1]:pid, line[4]:fd
          #print(fd_inode)
      
        elif (line[2]=='fork') or(line[2]=='clone'):
          ppid[line[3]] = line[1] # {'pid':'ppid'}

        elif (line[2]=='fstat'):
          if line[4]=='0' or line[4]=='1' or line[4]=='2':  # stdinput, stdoutput, stderror
            continue
          try:
            filename = fd_inode.pop(line[1]+","+line[4])  # line[1]:pid, line[4]:fd
            if (not (filename in file_inode.keys())) or (filename.find('manually') != -1):
              file_inode[filename] = random_str(12)    # use random string as file inode
          except KeyError:  # try to get inode of closed file state or already done 'fstat'
            try: # fstat on parent fd
              parent = ppid[line[1]]
              filename = fd_inode.pop(parent+","+line[4])
              if not filename in file_inode.keys():
                file_inode[filename] = random_str(12)
            except KeyError: # not child process
              continue
      
        elif (line[2]=='stat') or (line[2]=='lstat'):
          if not line[8] in file_inode.keys():
            file_inode[line[8]] = line[9] # line[8]:filename, line[9]:inode

        elif (line[2]=='close'):
          try:
            # close file without running 'fstat'
            filename = fd_inode.pop(line[1]+","+line[4])  # line[1]:pid, line[4]:fd
            # assign random string as file inode
            file_inode[filename] = random_str(12)
          except KeyError:  # done fstat already
            continue
  
  # files without running 'close'
  for pid_fd, filenames in fd_inode.items():
      if not (filenames in file_inode):
        file_inode[filenames] = random_str(12)
  
  # save file-inode list
  wf = open(args.output, 'w')

  for filenames, inodes in file_inode.items():
    # save
    wf.write('"'+filenames+'",'+inodes+'\n')

  wf.close()

