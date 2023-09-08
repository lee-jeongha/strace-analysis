class LRUCache(object):
    def __init__(self, max_cache_size=float("inf")):
        self.cache = []
        self.max_cache_size = max_cache_size
        self.in_cache_size = 0
        self.fault_cnt = 0

    def get(self):
        return self.cache, self.in_cache_size

    def set(self, cache):
        self.cache = cache
        self.in_cache_size = len(cache)

    def reference(self, ref_address):
        if ref_address in self.cache:
            rank = self.cache.index(ref_address)
            if rank == 0:
                return rank
            else:
                _ = self.cache.pop(rank)
                self.cache.insert(0, ref_address)
                return rank

        else:
            self.fault_cnt += 1
            if self.in_cache_size >= self.max_cache_size:
                self.evict()
            self.cache.insert(0, ref_address)
            self.in_cache_size += 1
            return -1

    def evict(self):
        _ = self.cache.pop()
        self.in_cache_size -= 1

if __name__ == "__main__":
    lru_cache = LRUCache(max_cache_size=6)
    #lru_cache.set([0, 1, 3, 4, 2])
    lru_cache.reference(2)
    lru_cache.reference(4)
    lru_cache.reference(3)
    lru_cache.reference(1)
    lru_cache.reference(0)

    lru_cache.reference(2)
    print(lru_cache.get())

    lru_cache.reference(7)
    print(lru_cache.get())

    lru_cache.reference(5)
    print(lru_cache.get())

    lru_cache.reference(4)
    print(lru_cache.get())

    lru_cache.reference(6)
    print(lru_cache.get())