import pandas as pd
import time
import heapq

class LFUCacheHeap(object):
    def __init__(self, max_cache_size):
        self.cache = {}  # {addr: lfu_element, }, which `lfu_element` is [acc_count, addr]
        self.lfu_heap = [] # [[acc_count, addr], ...]
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
            addr, acc_info = key, value
            lfu_heap.append(acc_info)
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
            ref_info = self.cache[ref_address]
            idx = self.lfu_heap.index(ref_info)
            updates = [ref_info[0] + 1, ref_address]    # update reference count
            self.cache[ref_address] = updates
            self.lfu_heap[idx] = updates

            # if new node is larger than left child or right child
            self.heap_sort(idx)

            return idx  # not an exact rank

        else:
            self.fault_cnt += 1
            updates = [1, ref_address]
            if len(self.cache) >= self.max_cache_size:
                #heapq.heapreplace(self.lfu_heap, updates)
                evicted = heapq.heappop(self.lfu_heap)
                _ = self.cache.pop(evicted[1], None)
            self.cache[ref_address] = updates
            heapq.heappush(self.lfu_heap, updates)
            #idx = self.lfu_heap.index(updates)

            return -1
#-------------------------------------------------------
class FileBlock:
    def __init__(self, blknum, last_ref_vtime=0, reference_cnt=0, inode=-1):
        self.addr = blknum
        self.last_ref_vtime = last_ref_vtime
        self.modified_bit = 0    # dirty bit
        self.reference_cnt = reference_cnt
        self.inode = inode

    def set_modified(self, bit=1):
        self.modified_bit = bit

    def set_reference(self, vtime):
        self.reference_cnt += 1
        self.last_ref_vtime = vtime

    def __hash__(self):
        '''
        >>> d = { FileBlock(0): 0, FileBlock(2): 2, FileBlock(7): 7 }
        >>> type(d)
        <class 'dict'>
        >>> d
        {<__main__.FileBlock object at 0x747a258635d0>: 0, <__main__.FileBlock object at 0x747a25863810>: 2, <__main__.FileBlock object at 0x747a25874050>: 7}
        '''
        return hash(self.addr)

    def __eq__(self, other):
        '''
        Dunder(double underbar) method in Python classes which defines the functionality of the equality operator (==)
        * The `FileBlock` class checks the equivalence of elements in either `int` or `FileBlock` classes
        >>> a = FileBlock(7)
        >>> b = FileBlock(6)
        >>> c = FileBlock(7)
        >>> a == b
        False
        >>> a == c
        True
        >>> a == 7
        True
        '''
        try:
            return (self.addr == other.addr)
        except:
            return (self.addr == other)

    def __lt__(self, other):
        '''
        Defines behavior for the less-than operator (<)
        '''
        try:
            if (self.reference_cnt < other.reference_cnt):
                return True
            elif (self.reference_cnt == other.reference_cnt): # Tie!!!
                # Tie_breaker
                # -> The larger the last reference time, the higher the value is considered to be
                if (self.last_ref_vtime < other.last_ref_vtime):
                    return True
            return False

        except:
            return self.reference_cnt < other

    def __gt__(self, other):
        '''
        Defines behavior for the greater-than operator (>)
        '''
        try:
            if (self.reference_cnt > other.reference_cnt):
                return True
            elif (self.reference_cnt == other.reference_cnt): # Tie!!!
                # Tie_breaker
                # -> The larger the last reference time, the higher the value is considered to be
                if (self.last_ref_vtime > other.last_ref_vtime):
                    return True
            return False

        except:
            return self.reference_cnt > other

class LFUCacheHeapTieBreak(LFUCacheHeap):
    def __init__(self, max_cache_size):
        self.cache = {}  # {addr: file_block}
        self.lfu_heap = [] # [file_block, ...]
        self.max_cache_size = max_cache_size
        self.in_cache_size = 0
        self.fault_cnt = 0
        self.cur_vtime = 0

    def heap_sort(self, idx):
        # if new node is larger than left child or right child
        left = idx * 2 + 1
        right = idx * 2 + 2
        s_idx = idx
        if (left < len(self.lfu_heap)) \
            and (self.lfu_heap[s_idx] > self.lfu_heap[left]):
            s_idx = left

        if (right < len(self.lfu_heap)) \
            and (self.lfu_heap[s_idx] > self.lfu_heap[right]):
            s_idx = right

        if s_idx != idx:
            self.lfu_heap[idx], self.lfu_heap[s_idx] = self.lfu_heap[s_idx], self.lfu_heap[idx]
            return self.heap_sort(s_idx)

    def reference(self, ref_address):
        #self.cur_vtime -= 1    # tie_breaker == MRU: negative virtual_time
        self.cur_vtime += 1    # tie_breaker == LRU: positive virtual_time

        if ref_address in self.cache.keys():
            ref_info = self.cache[ref_address]
            idx = self.lfu_heap.index(ref_info)

            # update reference count and current virtual time
            ref_info.set_reference(self.cur_vtime)
            assert (self.lfu_heap[idx].reference_cnt == self.cache[ref_address].reference_cnt and self.cache[ref_address].reference_cnt > 1) and (self.lfu_heap[idx].last_ref_vtime == self.cache[ref_address].last_ref_vtime)

            # if new node is larger than left child or right child
            self.heap_sort(idx)

            return idx  # not an exact rank

        else:
            self.fault_cnt += 1
            updates = FileBlock(blknum=ref_address, last_ref_vtime=self.cur_vtime, inode=-1, reference_cnt=1)
            if len(self.cache) >= self.max_cache_size:
                #heapq.heapreplace(self.lfu_heap, updates)
                evicted = heapq.heappop(self.lfu_heap)
                _ = self.cache.pop(evicted.addr, None)
            self.cache[ref_address] = updates
            heapq.heappush(self.lfu_heap, updates)

            return -1

#-------------------------------------------------------
def access_to_lfu_buffer(df, lfu_cache):
    s_time = time.time()
    for index, row in df.iterrows():  ### one by one
        ### Increase readcnt/writecnt by matching block_rank
        acc_rank = lfu_cache.reference(row['blocknum'])

    return lfu_cache


def lfu_buffer_simulation(df, cache_sizes, filename):
    fault_cnt = []

    for i in range(len(cache_sizes)):
        lfu_cache = LFUCacheHeap(max_cache_size = cache_sizes[i])
        lfu_cache = access_to_lfu_buffer(df, lfu_cache)
        fault_cnt.append(lfu_cache.fault_cnt)
        print(i, "buffer_simulation: cache_size", cache_sizes[i] , "done\t", fault_cnt[-1], sep=' ')

    results_df = pd.DataFrame.from_dict({'fault_cnt':fault_cnt, 'ref_cnt':[df.shape[0]]*len(cache_sizes), 'cache_size':cache_sizes})
    results_df.to_csv(filename+'-lfu_faultcnt_simulation.csv')
    
    return fault_cnt

def mp_lfu_buffer_simulation(idx, df, fault_cnt, ref_cnt, cache_sizes):
    cache_size = cache_sizes[idx]
    lfu_cache = LFUCacheHeap(max_cache_size = cache_size)
    #lfu_cache = LFUCacheHeapTieBreak(max_cache_size = cache_size)
    lfu_cache = access_to_lfu_buffer(df, lfu_cache)
    fault_cnt[idx] = lfu_cache.fault_cnt
    ref_cnt[idx] = df.shape[0]
    print(idx, "buffer_simulation: cache_size", cache_size , "done\t", lfu_cache.fault_cnt, sep=' ')
