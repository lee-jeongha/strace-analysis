import argparse
import csv
import os
import subprocess   # to get cmd results

parser = argparse.ArgumentParser()
parser.add_argument("input", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("output", metavar='O', type=str, nargs='?', default='output.txt', help='output file')

args = parser.parse_args()


with open(args.input) as rf:
    reader=csv.reader(rf, delimiter=',')
    
    fd_inode = dict() # {'pid,fd':'filename'}, for on-line tracking
    file_inode = dict() # {'filename':pid}, for saving

    for i, line in enumerate(reader):
      #print(line)
      if (line[2]=='open') or (line[2]=='openat') or (line[2]=='creat'):
        fd_inode[line[1]+","+line[3]] = line[7]  # line[1]:pid, line[3]:fd
        #print(fd_inode)
      
      elif (line[2]=='fstat'):
        if line[3]=='0' or line[3]=='1' or line[3]=='2':  # stdinput, stdoutput, stderror
          continue
        try:
          filename = fd_inode.pop(line[1]+","+line[3])  # line[1]:pid, line[3]:fd
          file_inode[filename] = line[8]    # line[8]:inode
        except KeyError:  # try to get inode of closed file state or already done 'fstat'
          continue
      
      elif (line[2]=='close'):
        try:
          # close file without running 'fstat'
          filename = fd_inode.pop(line[1]+","+line[3])  # line[1]:pid, line[3]:fd
          # find inode manually
          if not (filename in file_inode):
            stat_cmd = "stat "+filename+" | grep Inode | awk '{print $4}'"
            inode = str(subprocess.getstatusoutput(stat_cmd)[1])  # str(os.system(stat_cmd))
            file_inode[filename] = inode+'-manually_found'
            print('"'+filename+'",'+inode+'-manually_found\n')
        except KeyError:  # done fsat already
          continue

# files without running 'close'
for pid_fd, filenames in fd_inode.items():
    if not (filenames in file_inode):
      stat_cmd = "stat "+filenames+" | grep Inode | awk '{print $4}'"
      inode = str(subprocess.getstatusoutput(stat_cmd)[1])  # str(os.system(stat_cmd))
      file_inode[filenames] = inode+'-manually_found-unclosed'
      print('"'+filenames+'",'+inode+'-manually_found-unclosed\n')

# save file-inode list
wf = open(args.output, 'w')
for filenames,inodes in file_inode.items():
  wf.write('"'+filenames+'",'+inodes+'\n')
wf.close()
