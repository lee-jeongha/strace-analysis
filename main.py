from utils import load_json, save_json, save_csv

import math
import pandas as pd
import multiprocessing as mp
import matplotlib.pyplot as plt

def parse_strace_log(input_filename, output_filename, sep=','):
    from stcparse import parse_syscall_line

    rf = open(input_filename, 'r')
    rlines = rf.readlines()
    wf = open(output_filename+'.csv', 'w')

    global unfinished_dict
    unfinished_dict = dict()  # for '<unfinished ...>' log

    for line in rlines:
        line = line.strip("\n")  # remove '\n'

        wlines = parse_syscall_line(line)
        if wlines == 0:
            continue
        elif wlines == -1:
            print("error on :", line)
            continue
        wf.write(sep.join(wlines) + "\n")

    rf.close()
    wf.close()

def extract_fileio_trace(input_filename, inode_filename, interim_filename, output_filename, fig_title, sep=','):
    from fileio import save_filename_inode_list
    from fileio import save_file_reference
    from fileio import save_fileref_in_blocksize, plot_ref_addr_graph

    save_filename_inode_list(input_filename, inode_filename, delimiter=sep, numeric_only=True)

    save_file_reference(input_filename, inode_filename, interim_filename, inputfile_delimiter=sep)

    blkdf = save_fileref_in_blocksize(interim_filename, inode_filename, output_filename, blocksize=4096, inodefile_delimiter=sep, redundant_files=[], redundant_pids=[])
    #blkdf = pd.read_csv(output_filename+'.csv')
    plot_ref_addr_graph(blkdf, fig_title, output_filename)

def block_distribution(input_filename, output_filename, fig_title):
    from fileio.statistics import ref_cnt_per_block, plot_ref_cnt_graph

    ## use list of chunk
    blkdf = pd.read_csv(input_filename+'.csv', sep=',', chunksize=1000000, header=0, index_col=0, on_bad_lines='skip')
    df1 = ref_cnt_per_block(blkdf_list=list(blkdf))
    save_csv(df1, output_filename+'.csv', 0)

    #df1 = pd.read_csv(output_filename+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')
    plot_ref_cnt_graph(blkdf=df1, fig_title=fig_title, filename=output_filename)

def block_popularity(input_filename, output_filename, fig_title, zipf=False):
    from fileio.statistics import ref_cnt_rank, ref_cnt_percentile_rank, popularity_graph, cdf_graph

    #tendency of memory block access
    blkdf2 = pd.read_csv(input_filename+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')

    blkdf2 = ref_cnt_rank(blkdf2)
    blkdf2 = ref_cnt_percentile_rank(blkdf2)
    save_csv(blkdf2, output_filename+'.csv', 0)

    #blkdf2 = pd.read_csv(output_filename+'.csv', sep=',', header=0, index_col=0, on_bad_lines='skip')

    popularity_graph(blkdf=blkdf2, filename=output_filename, fig_title=fig_title, zipf=zipf, single_frame=False)
    plt.cla()
    cdf_graph(blkdf=blkdf2, fig_title=fig_title, filename=output_filename)

def estimator_simulation(estimator_type, start_chunk, input_filename, output_filename):
    from fileio.simulator.estimator import LRUCache, LFUCacheList
    from fileio.simulator.estimator import mp_estimator_simulation
    from fileio.simulator import estimator_graph_by_operation

    endpoint_q = mp.Queue()
    processes = []
    operations = ['read', 'write', 'all']
    endpoints, ref_cnts = [], []

    assert (estimator_type == 'recency' or estimator_type == 'frequency')

    if not start_chunk:
        suffix = "-"+estimator_type+"_estimator_simulation"
    else:
        end_chunk = endpoints[0]
        suffix = "_checkpoint" + str(end_chunk) + "-"+estimator_type+"_estimator_simulation"

    if estimator_type == 'recency':
        ref_block = LRUCache()
    else:
        ref_block = LFUCacheList()

    for op in operations:
        p = mp.Process(target=mp_estimator_simulation, args=(ref_block, start_chunk, endpoint_q, input_filename, output_filename+suffix, op))
        processes.append(p)
        p.start()

    # get return value
    for p in processes:
        endpoints.append(endpoint_q.get())

    for p in processes:
        p.join()

    for op in operations:
        filename = output_filename + suffix + "-" + op + ".json"
        _, ref_cnt = load_json(['block_rank', 'ref_cnt'], filename)
        ref_cnts.append(ref_cnt)
    #estimator_graph_by_operation(read_cnt=ref_cnts[0], write_cnt=ref_cnts[1], total_cnt=ref_cnts[2], title=args.title, filename=output_filename+suffix)

def buffer_cache_simulation(buffer_type, input_filename, output_filename, fig_title):
    from fileio.simulator.buffer_cache import (
        mp_lru_buffer_simulation, lru_buffer_simulation,
        mp_lfu_buffer_simulation, lfu_buffer_simulation,
        #mp_mru_buffer_simulation, mru_buffer_simulation,
    )
    from fileio.simulator import _buffer_cache_graph

    assert (buffer_type == 'lru' or buffer_type == 'lfu' or buffer_type == 'mru')
    suffix = "-"+buffer_type+"_buffer_simulation"

    if buffer_type == 'lru':
        mp_buffer_simulation = mp_lru_buffer_simulation
        buffer_simulation = lru_buffer_simulation
    elif buffer_type == 'lfu':
        mp_buffer_simulation = mp_lfu_buffer_simulation
        buffer_simulation = lfu_buffer_simulation
    #elif buffer_type == 'mru':
    #    mp_buffer_simulation = mp_mru_buffer_simulation
    #    buffer_simulation = mru_buffer_simulation

    blkdf = pd.read_csv(input_filename + '.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')

    block_num = len(pd.unique(blkdf['blocknum']))

    cache_sizes = [round(block_num * 0.1 * i) for i in range(1, 10)]

    #===== multiprocessing =====#
    n_nodes = len(cache_sizes);    p_num = 3;    processes = []
    fault_cnt = mp.Array('i', range(n_nodes));    ref_cnt = mp.Array('i', range(n_nodes));    max_size = mp.Array('i', range(n_nodes))

    for i in range(math.ceil(n_nodes/p_num)):
        for j in range(p_num):
            if ((i * p_num + j) >= n_nodes):
                break
            print("start process:", (i * p_num + j))
            process = mp.Process(target=mp_buffer_simulation, args=(i * p_num + j, blkdf, fault_cnt, ref_cnt, cache_sizes))
            processes.append(process)
            process.start()
        
        for p in processes:
            p.join()

    print(cache_sizes)
    print(fault_cnt[:])
    f = open(output_filename + suffix + '.csv', 'w')
    f.write('fault_cnt,ref_cnt,cache_size,block_num\n')
    for i in range(len(fault_cnt)):
        f.write(str(fault_cnt[i])+','+str(ref_cnt[i])+','+str(cache_sizes[i])+','+str(block_num)+'\n')
    f.close()

    #===== single-processing =====#
    #fault_cnt = buffer_simulation(df=blkdf, cache_sizes=cache_sizes, filename=output_filename)

    #===== =====#
    '''df_buf = pd.read_csv(output_filename+suffix+'.csv', sep=',', header=0, index_col=None, on_bad_lines='skip')
    fault_cnt = df_buf['fault_cnt']; ref_cnt = df_buf['ref_cnt'];   cache_sizes = df_buf['cache_size']'''

    #===== plot-graph =====#
    '''_buffer_cache_graph([i * 100 // len(cache_sizes) for i in range(1, len(cache_sizes)+1)], [i / blkdf.shape[0] * 100 for i in miss_cnt],
                         title=fig_title, filename=output_filename+suffix, ylim=[0,100])'''


if __name__=="__main__":
    # add parser
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file path')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file path')
    parser.add_argument("--title", "-t", metavar='T', type=str,
                        nargs='?', default='', help='title of figures')
    parser.add_argument("--blocksize", "-b", metavar='B', type=int,
                        nargs='?', default=4096, help='block size')
    args = parser.parse_args()

    # check if the output path exists
    import os
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"Make directory: {args.output}")

    #-----
    parse_strace_log(input_filename=args.input, output_filename=args.output+'/'+'0parse', sep='\t')
    extract_fileio_trace(input_filename=args.output+'/'+'0parse', inode_filename=args.output+'/'+'1inode',
                         interim_filename=args.output+'/'+'2fileref', output_filename=args.output+'/'+'fileio.strace',
                         fig_title=args.title, sep='\t')
    block_distribution(input_filename=args.output+'/'+'fileio.strace', output_filename=args.output+'/'+'blkdf1', fig_title=args.title)
    block_popularity(input_filename=args.output+'/'+'blkdf1', output_filename=args.output+'/'+'blkdf2', fig_title=args.title, zipf=False)

    #-----
    from fileio.simulator import buffer_cache_graph

    buffer_cache_prefix = args.output+'/'+'blkdf3'
    suffix = "_buffer_simulation"
    for bt in ['lru', 'lfu']:
        buffer_cache_simulation(buffer_type=bt, input_filename=args.output+'/'+'fileio.strace', output_filename=buffer_cache_prefix, fig_title=args.title)

    lru_filename = buffer_cache_prefix + '-lru' + suffix + '.csv'
    lru_df = pd.read_csv(lru_filename)

    lfu_filename = buffer_cache_prefix + '-lfu' + suffix + '.csv'
    lfu_df = pd.read_csv(lfu_filename)

    buffer_cache_graph(lru_df=lru_df, lfu_df=lfu_df, title=args.title, filename=buffer_cache_prefix)

    #-----
    from fileio.simulator import estimator_graph

    estimator_prefix = args.output+'/'+'blkdf4'
    suffix = "_estimator_simulation-all"
    for et in ['recency', 'frequency']:
        estimator_simulation(estimator_type=et, start_chunk=0, input_filename=args.output+'/'+'fileio.strace', output_filename=estimator_prefix)

    recency_filename = estimator_prefix + '-recency' + suffix + '.json'
    _, recency_ref_cnt = load_json(['block_rank', 'ref_cnt'], recency_filename)

    frequency_filename = estimator_prefix + '-frequency' + suffix + '.json'
    _, frequency_ref_cnt = load_json(['block_rank', 'ref_cnt'], frequency_filename)

    estimator_graph(recency_cnt=recency_ref_cnt, frequency_cnt=frequency_ref_cnt, title=args.title, filename=estimator_prefix)