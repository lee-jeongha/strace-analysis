#!/bin/bash

# options:
INPUT_FILE=""
OUTPUT_DIR=""
STRACE=""
FILE_IO=False
RANDOM_INODE=False

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
        -f|--file)
            FILE_IO=True
            shift
            ;;
        -r|--random_inode)
            RANDOM_INODE=True
            shift
            ;;
        -h|--help)
            echo "Usage:  $0 -i <input> [options]" >&2
            echo "        -i | --input  %  (input file name)" >&2
            echo "        -o | --output  %  (output directory name)" >&2
            echo "        -s | --strace  %   (process to use strace)" >&2
            echo "        -f | --file     (whether analyze file IO or not)" >&2
            echo "        -r | --random_inode     (whether assign random inode or not)" >&2
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
CODE_PATH=${0:0:-7}

# strace
if [[ -n "$STRACE" ]]; then
    strace -a1 -s0 -f -C -tt -e trace=read,write,pread64,pwrite64,lseek,mmap,munmap,mremap,creat,open,openat,close,stat,fstat,lstat,fork,clone -o $INPUT_FILE $STRACE
    echo =====running strace \'$STRACE\' is done!=====
fi;

# make directory
mkdir $OUTPUT_DIR
echo =====making \'$OUTPUT_DIR\' is done!=====

# parsing
python3 $CODE_PATH/stcparse.py -i $INPUT_FILE -o $OUTPUT_DIR/0parse.csv
echo =====parsing is done!=====

# when anaylzing file io
if [ $FILE_IO ]; then
    if [ $RANDOM_INODE ]; then
        python3 $CODE_PATH/fileio/1fileinode.py --random_inode -i $OUTPUT_DIR/0parse.csv -o $OUTPUT_DIR/1-1inode.csv
    else
        python3 $CODE_PATH/fileio/1fileinode.py -i $OUTPUT_DIR/0parse.csv -o $OUTPUT_DIR/1-1inode.csv
    fi;
    python3 $CODE_PATH/fileio/2filetrace.py -i $OUTPUT_DIR/0parse.csv -o $OUTPUT_DIR/1-2fileio.csv -f $OUTPUT_DIR/1-1inode.csv
    python3 $CODE_PATH/fileio/3filerefblk.py -i $OUTPUT_DIR/1-2fileio.csv -o $OUTPUT_DIR/2fileblk.csv
    echo =====preprocessing is done!=====

    # plot graph
    python3 $CODE_PATH/fileio/plot/1refcountperblock.py -i $OUTPUT_DIR/2fileblk.csv -o $OUTPUT_DIR/blkdf1.csv
    python3 $CODE_PATH/fileio/plot/2popularity.py -i $OUTPUT_DIR/blkdf1.csv -o $OUTPUT_DIR/blkdf2.csv
    python3 $CODE_PATH/fileio/plot/3blkaccess.py -i $OUTPUT_DIR/2fileblk.csv -o $OUTPUT_DIR/blkdf3.csv
    echo =====plotting is done!=====

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
