#!/bin/bash

# options:
INPUT_FILE=""
OUTPUT_DIR=""
STRACE=""
TITLE=""
FILE_IO=False
RANDOM_INODE=False
BLOCKSIZE=""

# get options:
while (( "$#" )); do
    case "$1" in
        -i|--input)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                INPUT_FILE=$2
                shift 2
            else
                echo "Error: Argument for $1 is missing" >&2
                exit 1
            fi
            ;;
        -o|--output)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                OUTPUT_DIR=$2
                shift 2
            else
                echo "Error: Argument for $1 is missing" >&2
                exit 1
            fi
            ;;
        -s|--strace)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                STRACE=$2
                shift 2
            else
                echo "Error: Argument for $1 is missing" >&2
                exit 1
            fi
            ;;
        -t|--title)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                TITLE=$2
                shift 2
            else
                echo "Error: Argument for $1 is missing" >&2
                exit 1
            fi
            ;;
        -f|--file)
            FILE_IO=True
            shift
            ;;
        -b|--blocksize)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                BLOCKSIZE=$2
                shift 2
            else
                echo "Error: Argument for $1 is missing" >&2
                exit 1
            fi
            ;;
        -h|--help)
            echo "Usage:  $0 -i <input> [options]" >&2
            echo "        -i | --input  %  (input file name)" >&2
            echo "        -o | --output  %  (output directory name)" >&2
            echo "        -s | --strace  %   (process to track with strace)" >&2
            echo "        -t | --title  %   (title of graphs)" >&2
            echo "        -f | --file     (whether analyze file IO or not)" >&2
            echo "        -b | --blocksize  %   (blocksize, default: 4KB)" >&2
            exit 0
            ;;
        -*|--*) # unsupported flags
            echo "Error: Unsupported flag: $1" >&2
            echo "$0 -h for help message" >&2
            exit 1
            ;;
        *)
            echo "Error: Arguments with not proper flag: $1" >&2
            echo "$0 -h for help message" >&2
            exit 1
            ;;
    esac
done

# find path
#CODE_PATH=${0:0:-7}
CODE_PATH=${0:0:$((${#0} - 0 - 7))}

# strace
if [[ -n "$STRACE" ]]; then
    strace -a1 -s0 -f -C -tt -v -yy -z -e trace=read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,memfd_create,close,stat,fstat,lstat,fork,clone,socket,socketpair,pipe,pipe2,dup,dup2,dup3,fcntl,eventfd,eventfd2 -o $INPUT_FILE $STRACE
    echo =====running strace \'$STRACE\' is done!=====
fi;
# make directory
mkdir $OUTPUT_DIR
echo =====making \'$OUTPUT_DIR\' is done!=====

# analyze strace log
python3 $CODE_PATH/main.py -i $INPUT_FILE -o $OUTPUT_DIR -t $TITLE -b $BLOCKSIZE

:<<'END'
    # block access per real time
    columns=(7 8)
    gnuplot << EOF
      set datafile separator ','
      set title "reference block"
      set xlabel "time"
      set ylabel "block number"
      set term png size 1500,1100
      set output "$OUTPUT_DIR/2fileblk.png"
      plot "$OUTPUT_DIR/2fileblk.csv" using 2:7 lt rgb "blue" title "read",\
    "$OUTPUT_DIR/2fileblk.csv" using 2:8 lt rgb "red" title "write"
    EOF
END

fi;
