import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("input", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("output", metavar='O', type=str, nargs='?', default='output.txt', help='output file')

args = parser.parse_args()


wf = open(args.output, 'w')
with open(args.input) as rf:
    reader=csv.reader(rf, delimiter=',')
    
    fd_inode = dict() # {'pid,fd':'filename'}, for on-line tracking
    
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
          wf.write('"'+filename+'",'+line[8]+'\n')  # file_inode[0]:filename, line[8]:inode
        except KeyError:  # try to get closed file state 
          continue
      
      elif (line[2]=='close'):
        try:
          filename = fd_inode.pop(line[1]+","+line[3])  # line[1]:pid, line[3]:fd
          wf.write('"'+filename+'",'+'not_found\n')  # file_inode[0]:filename, line[8]:inode
        except KeyError:  # already closed
          continue
        #except IndexError:  # close file without running fstat
          #inode_info[file_inode[0]] = 'not_found'   # file_inode[0]:filename, 'none':inode'''

print(fd_inode)
for pid_fd, filenames in fd_inode.items():
  wf.write('"'+filenames+'",'+'not_found-unclosed'+"\n")
wf.close()
