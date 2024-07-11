import pandas as pd
import numpy as np
from functools import lru_cache

#-----
def lru_buffer_simulation(df, cache_sizes, filename):
    cache_info = []

    for i in range(len(cache_sizes)):
        @lru_cache(maxsize=cache_sizes[i])
        def access_cache(blocknum):
            return 1

        for index, row in df.iterrows():  ### one by one
            access_cache(row['blocknum'])

        cache_info.append(access_cache.cache_info())
        print("buffer_simulation: cache_size", cache_sizes[i] , "done\t", cache_info[-1], sep=' ')
        access_cache.cache_clear()

    cache_info = np.array(cache_info)
    df = pd.DataFrame.from_dict({'fault_cnt':cache_info[:,1], 'ref_cnt':[df.shape[0]]*len(cache_sizes), 'cache_size':cache_sizes})
    df.to_csv(filename+'-lru_faultcnt_simulation.csv')
    
    return cache_info[:,1]

def mp_lru_buffer_simulation(idx, df, fault_cnt, ref_cnt, cache_sizes):
    cache_size = cache_sizes[idx]

    @lru_cache(maxsize=cache_size)
    def access_cache(blocknum):
        return 1

    for index, row in df.iterrows():  ### one by one
        access_cache(row['blocknum'])

    cache_info = access_cache.cache_info()
    fault_cnt[idx] = cache_info[1]
    ref_cnt[idx] = df.shape[0]

    print(idx, "buffer_simulation: cache_size", cache_size , "done\t", cache_info[1], sep=' ')
    access_cache.cache_clear()
