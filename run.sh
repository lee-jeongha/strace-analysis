#!/bin/bash

# options:
INPUT_FILE=""
OUTPUT_DIR=""
RANDOM=False

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
        -r|--random_inode)
	    RANDOM=True
	    shift
	    ;;
        -h|--help)
            echo "Usage:  $0 -i <input> [options]" >&2
            echo "        -i | --input  %  (set input file name)" >&2
            echo "        -o | --output  %  (set output directory name)" >&2
            echo "        -r | --random_inode     (assign random inode)" >&2
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

# make directory
#target=$2
mkdir $OUTPUT_DIR
echo =====making $OUTPUT_DIR is done!=====

# 
python3 stcparse.py -i $INPUT_FILE -o $OUTPUT_DIR/0parse.csv
if [ RANDOM ]; then
    python3 fileinode.py --random_inode -i $OUTPUT_DIR/0parse.csv -o $OUTPUT_DIR/1-1inode.csv
else
    python3 fileinode.py -i $OUTPUT_DIR/0parse.csv -o $OUTPUT_DIR/1-1inode.csv
fi;
python3 filetrace.py -i $OUTPUT_DIR/0parse.csv -o $OUTPUT_DIR/1-2fileio.csv -f $OUTPUT_DIR/1-1inode.csv
python3 filerefblk.py -i $OUTPUT_DIR/1-2fileio.csv -o $OUTPUT_DIR/2fileblk.csv

# memory access per logical time
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

