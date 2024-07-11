import pandas as pd
import numpy as np
from cacheout.mru import MRUCache

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from plot_graph import plot_frame

#-----
def mru_buffer_simulation(df, cache_sizes, filename):
    mru_cache = MRUCache()
    cache_info = []

    for i in range(len(cache_sizes)):
        mru_cache = MRUCache(maxsize=i, enable_stats=True)
        @mru_cache.memoize()
        def access_cache(blocknum):
            return 1

        for index, row in df.iterrows():  ### one by one
            access_cache(row['blocknum'])

        # 'hit_count', 'miss_count', 'eviction_count', 'entry_count', 'access_count', 'hit_rate', 'miss_rate', 'eviction_rate'
        cache_stats = access_cache.cache.stats.info().to_dict()
        cache_info.append([cache_stats['miss_count'], cache_stats['access_count'], cache_stats['entry_count']])

        print("buffer_simulation: cache_size", cache_sizes[i] , "done\t", cache_info[-1], sep=' ')
        access_cache.cache.clear()

    cache_info = np.array(cache_info)
    df = pd.DataFrame.from_dict({'fault_cnt':cache_info[:,1], 'ref_cnt':[df.shape[0]]*len(cache_sizes), 'cache_size':cache_sizes})
    df.to_csv(filename+'-mru_faultcnt_simulation.csv')

    return cache_info[:, 1]

def mp_mru_buffer_simulation(idx, df, fault_cnt, ref_cnt, cache_sizes):
    cache_size = cache_sizes[idx]

    mru_cache = MRUCache(maxsize=cache_size, enable_stats=True)
    @mru_cache.memoize()
    def access_cache(blocknum):
        return 1

    for index, row in df.iterrows():  ### one by one
        access_cache(row['blocknum'])

    # 'hit_count', 'miss_count', 'eviction_count', 'entry_count', 'access_count', 'hit_rate', 'miss_rate', 'eviction_rate'
    cache_stats = access_cache.cache.stats.info().to_dict()
    fault_cnt[idx] = cache_stats['miss_count']
    ref_cnt[idx] = cache_stats['access_count']

    print(idx, "buffer_simulation: cache_size", cache_size , "done\t", cache_stats['miss_count'], sep=' ')
    access_cache.cache.clear()
