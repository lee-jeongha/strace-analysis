import random

class FreqNode(object):
    def __init__(self, freq, ref_block, pre, nxt):
        self.freq = freq
        self.ref_block = ref_block
        self.pre = pre  # previous FreqNode
        self.nxt = nxt  # next FreqNode

    def count_blocks(self):
        return len(self.ref_block)

    def remove(self):
        if self.pre is not None:
            self.pre.nxt = self.nxt
        if self.nxt is not None:
            self.nxt.pre = self.pre

        pre = self.pre
        nxt = self.nxt
        self.pre = self.nxt = None

        return (pre, nxt)

    def remove_block(self, ref_address): # remove ref_address from ref_block within freq_node
        ref_address_idx = self.ref_block.index(ref_address)
        _ = self.ref_block.pop(ref_address_idx)

        return ref_address_idx

    def insert_ref_block(self, ref_address):
        self.ref_block.insert(0, ref_address)

    def append_ref_block(self, ref_address):
        self.ref_block.append(ref_address)

    def insert_after_me(self, freq_node):
        freq_node.pre = self
        freq_node.nxt = self.nxt

        if self.nxt is not None:
            self.nxt.pre = freq_node

        self.nxt = freq_node

    def insert_before_me(self, freq_node):
        if self.pre is not None:
            self.pre.nxt = freq_node

        freq_node.pre = self.pre
        freq_node.nxt = self
        self.pre = freq_node

#--------------------------------------------------------------------------------
class LFUCacheList(object):
    def __init__(self):
        self.cache = {}  # {addr: freq_node}
        self.freq_link_head = None

    def __len__(self):
        return len(self.cache)

    def get(self):
        ref_table = {}  # {freq: [ref_block]}
        current = self.freq_link_head

        while current != None:
            freq = current.freq
            ref_block = current.ref_block
            ref_table[freq] = ref_block
            current = current.nxt

        return ref_table

    def set(self, ref_table):
        freqs = list(ref_table.keys())
        freqs.sort()

        prev_freq_node = None
        for freq in freqs:
            ref_block = ref_table[freq]
            target_freq_node = FreqNode(freq, ref_block, None, None)

            if prev_freq_node == None:
                self.freq_link_head = target_freq_node
            else:
                target_freq_node.pre = prev_freq_node
                prev_freq_node.nxt = target_freq_node

            for ref_addr in ref_block:
                self.cache[ref_addr] = target_freq_node

            prev_freq_node = target_freq_node

    def test_print(self):
        current = self.freq_link_head
        while current != None:
            print(current.freq, current.ref_block)
            current = current.nxt

    def reference(self, ref_address):
        if ref_address in self.cache:
            freq_node = self.cache[ref_address]
            rank = self.get_freq_node_rank(freq_node)
            #rank += freq_node.ref_block.index(ref_address)

            new_freq_node = self.move_next_to(ref_address, freq_node)
            self.cache[ref_address] = new_freq_node

            return rank

        else:
            new_freq_node = self.create_freq_node(ref_address)
            self.cache[ref_address] = new_freq_node

            return -1

    def remove(self, ref_address):
        if ref_address in self.cache:
            freq_node = self.cache.pop(ref_address)

            if freq_node.count_blocks() == 1:
                if freq_node == self.freq_link_head:
                    self.freq_link_head = self.freq_link_head.nxt
                _ = freq_node.remove()
                
            else:
                _ = freq_node.remove_block(ref_address)

        else:
            print("Remove error!")

    def pop(self):
        victim_address = self.freq_link_head.ref_block[-1] # Tie breaker: LRU
        #victim_address = self.freq_link_head.ref_block[0] # Tie breaker: MRU
        #victim_address = min(self.freq_link_head.ref_block) # Tie breaker: min address
        #victim_address = random.choice(self.freq_link_head.ref_block) # Tie breaker: random choice

        freq_node = self.cache.pop(victim_address)

        if freq_node.count_blocks() == 0:
            self.freq_link_head = self.freq_link_head.nxt
            _ = freq_node.remove()

        return victim_address

    def move_next_to(self, ref_address, freq_node):  # for each access
        if freq_node.nxt is None or freq_node.nxt.freq != freq_node.freq + 1:
            target_freq_node = FreqNode(freq_node.freq + 1, list(), None, None)
            target_empty = True

        else:
            target_freq_node = freq_node.nxt
            target_empty = False

        target_freq_node.insert_ref_block(ref_address)

        if target_empty:
            freq_node.insert_after_me(target_freq_node)

        _ = freq_node.remove_block(ref_address)

        if freq_node.count_blocks() == 0: # if there is nothing left in freq_node
            if self.freq_link_head == freq_node:
                self.freq_link_head = target_freq_node

            freq_node.remove()
        
        return target_freq_node

    def create_freq_node(self, ref_address):
        ref_block = [ref_address]

        if self.freq_link_head is None or self.freq_link_head.freq != 1:
            new_freq_node = FreqNode(1, ref_block, None, None)
            self.cache[ref_address] = new_freq_node

            if self.freq_link_head is not None: # LFU has freq_link_head but frequency is not 1
                self.freq_link_head.insert_before_me(new_freq_node)

            self.freq_link_head = new_freq_node

            return new_freq_node

        else: # if LFU has freq_link_head which frequency value is 1
            self.freq_link_head.insert_ref_block(ref_address) #self.freq_link_head.append_ref_block(ref_address)

            return self.freq_link_head

    def get_freq_node_rank(self, freq_node):
        current = freq_node.nxt
        rank = 0

        while current != None:
            rank += current.count_blocks()
            current = current.nxt

        return rank

#--------------------------------------------------------------------------------
# LFU with aging
class LFUACacheList(LFUCacheList):
    def __init__(self):
        super().__init__()

    def aging(self):
        current = self.freq_link_head

        while current != None:
            current.freq /= 2
            current = current.nxt

#--------------------------------------------------------------------------------
# LFUDA (LFU with Dynamic Aging)
class LFUDACacheList(LFUCacheList):
    def __init__(self):
        super().__init__()
        self.age = 0

    def reference(self, ref_address):
        cache_age = self.age

        if ref_address in self.cache:
            freq_node = self.cache[ref_address]
            rank = self.get_freq_node_rank(freq_node)
            #rank += freq_node.ref_block.index(ref_address)

            if cache_age:
                self.remove(ref_address)
                new_freq_node = self.get_freq_node((freq_node.freq + 1) + cache_age)
                if isinstance(new_freq_node, FreqNode):#new_freq_node is not None:
                    new_freq_node.insert_ref_block(ref_address)
                else:
                    new_freq_node = self.insert_freq_node(ref_address, (freq_node.freq + 1) + cache_age)

            else:
                new_freq_node = self.move_next_to(ref_address, freq_node)

            self.cache[ref_address] = new_freq_node

            return rank

        else:
            if cache_age and self.freq_link_head is not None:
                new_freq_node = self.insert_freq_node(ref_address, (1) + cache_age)
            else:
                new_freq_node = self.create_freq_node(ref_address)

            self.cache[ref_address] = new_freq_node

            return -1

    def update_age(self):
    # For static aging
        if self.age == 0:
            self.age = 1
        else:
            self.age *= 2

    def insert_freq_node(self, ref_address, freq=1):
        # If freq == 1, use `self.create_feq_node()`
        assert freq > 1

        ref_block = [ref_address]

        new_freq_node = FreqNode(freq, ref_block, None, None)
        self.cache[ref_address] = new_freq_node

        current = self.freq_link_head
        if current.freq > freq:
            current.insert_before_me(new_freq_node)
            self.freq_link_head = new_freq_node
        else:
            while current != None:
                if (current.nxt is None) or (current.freq < freq and current.nxt.freq > freq):
                    break
                current = current.nxt

            current.insert_after_me(new_freq_node)

        return new_freq_node

    def get_freq_node(self, freq):
        current = self.freq_link_head
        while current != None:
            if current.freq == freq:
                break
            current = current.nxt

        return current

    def pop(self):
        victim_address = self.freq_link_head.ref_block[-1] # Tie breaker: LRU
        #victim_address = self.freq_link_head.ref_block[0] # Tie breaker: MRU
        #victim_address = min(self.freq_link_head.ref_block) # Tie breaker: min address
        #victim_address = random.choice(self.freq_link_head.ref_block) # Tie breaker: random choice

        freq_node = self.cache.pop(victim_address)

        self.age += freq_node.freq    # For dynamic aging
        _ = freq_node.remove_block(victim_address)

        if freq_node.count_blocks() == 0:
            self.freq_link_head = self.freq_link_head.nxt
            _ = freq_node.remove()

        return victim_address