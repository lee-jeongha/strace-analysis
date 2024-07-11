import pandas as pd
import time
import heapq

class LFUCache(object):
    def __init__(self, max_cache_size):
        self.cache = {}  # {addr: acc_count}
        self.lfu_heap = [] # [(acc_count, addr), ...]
        self.max_cache_size = max_cache_size
        self.in_cache_size = 0
        self.fault_cnt = 0

    def get(self):
        return self.cache, self.in_cache_size

    def set(self, cache):
        self.cache = cache
        self.in_cache_size = len(cache)

        lfu_heap = []
        for key, value in cache.items():
            addr, acc_count = key, value
            lfu_heap.append((acc_count, addr))
        self.lfu_heap = heapq.heapify(lfu_heap)

    def heap_sort(self, idx):
        # if new node is larger than left child or right child
        left = idx * 2 + 1
        right = idx * 2 + 2
        s_idx = idx
        if (left < len(self.lfu_heap)) and (self.lfu_heap[s_idx][0] > self.lfu_heap[left][0]):
            s_idx = left

        if (right < len(self.lfu_heap)) and (self.lfu_heap[s_idx][0] > self.lfu_heap[right][0]):
            s_idx = right

        if s_idx != idx:
            self.lfu_heap[idx], self.lfu_heap[s_idx] = self.lfu_heap[s_idx], self.lfu_heap[idx]
            return self.heap_sort(s_idx)

    def reference(self, ref_address):
        if ref_address in self.cache.keys():
            idx = self.lfu_heap.index((self.cache[ref_address], ref_address))
            ref_cnt = self.cache[ref_address] + 1
            updates = (ref_cnt, ref_address)
            self.cache[ref_address] = ref_cnt
            self.lfu_heap[idx] = updates

            # if new node is larger than left child or right child
            self.heap_sort(idx)

            return idx  # not an exact rank

        else:
            self.fault_cnt += 1
            updates = (1, ref_address)
            self.cache[ref_address] = 1
            if len(self.cache) >= self.max_cache_size:
                #heapq.heapreplace(self.lfu_heap, updates)
                evicted = heapq.heappop(self.lfu_heap)
                _ = self.cache.pop(evicted[1], None)
            heapq.heappush(self.lfu_heap, updates)

            return -1


def access_to_lfu_buffer(df, lfu_cache):
    s_time = time.time()
    for index, row in df.iterrows():  ### one by one
        assert (row['operation'] == 'read' or row['operation'] == 'write')

        ### Increase readcnt/writecnt by matching block_rank
        acc_rank = lfu_cache.reference(row['blocknum'])

        if index % 1000000 == 0:
            e_time = time.time()
            print(index, ":", e_time - s_time)

    return lfu_cache


def lfu_buffer_simulation(df, cache_sizes, filename):
    fault_cnt = []

    for i in range(len(cache_sizes)):
        lfu_cache = LFUCache(max_cache_size = cache_sizes[i])
        lfu_cache = access_to_lfu_buffer(df, lfu_cache)
        fault_cnt.append(lfu_cache.fault_cnt)
        print(i, "buffer_simulation: cache_size", cache_sizes[i] , "done\t", fault_cnt[-1], sep=' ')

    df = pd.DataFrame.from_dict({'fault_cnt':fault_cnt, 'ref_cnt':[df.shape[0]]*len(cache_sizes), 'cache_size':cache_sizes})
    df.to_csv(filename+'-lfu_faultcnt_simulation.csv')
    
    return fault_cnt

def mp_lfu_buffer_simulation(idx, df, fault_cnt, ref_cnt, cache_sizes):
    cache_size = cache_sizes[idx]
    lfu_cache = LFUCache(max_cache_size = cache_size)
    lfu_cache = access_to_lfu_buffer(df, lfu_cache)
    fault_cnt[idx] = lfu_cache.fault_cnt
    ref_cnt[idx] = df.shape[0]
    print(idx, "buffer_simulation: cache_size", cache_size , "done\t", lfu_cache.fault_cnt, sep=' ')
