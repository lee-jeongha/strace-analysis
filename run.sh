#!/bin/bash

# make directory
target=$2
mkdir $target
echo =====making $target is done!=====

# 
python3 stcparse.py $1 $target/0parse.csv
python3 fileinode.py $target/0parse.csv $target/1-1inode.csv
python3 filetrace.py $target/0parse.csv $target/1-2fileio.csv $target/1-1inode.csv
python3 filerefblk.py $target/1-2fileio.csv $target/2fileblk.csv

# memory access per logical time
gnuplot << EOF
  set datafile separator ','
  set title "reference block"
  set xlabel "time"
  set ylabel "block number"
  set term png
  set output "$target/2fileblk.png"
  plot "$target/2fileblk.csv" using 2:5
EOF

