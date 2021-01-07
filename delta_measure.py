'''
measures the rates of change of values given to it

measures deltas, not raw values

MODIFIED - above comment no longer correct
'''

#from scipy.stats import linregress
import numpy as np

class DeltaMeasure:
    def __init__(self, memory_length = 6, recency = 2):
        self.mem_len = memory_length
        self.recency = recency + 1
        self.mem_list = []
        self.rec_list = []
    
    def recent_size(self):
        # checks recent size across recency, then across recency -1 (to get better idea of 'latest' change)
        if len(self.mem_list) >= self.recency:
            self.rec_list = self.mem_list[-self.recency:]
            size = 0.
            for val in self.rec_list:
                size += val
            
            sm_size = 0.
            trunc_rec_list = self.rec_list[-2:]
            '''print('--')
            print(self.mem_list)
            print(self.rec_list)
            print(trunc_rec_list)
            print('--')'''
            for val in trunc_rec_list:
                sm_size += val
            """
            MAYBE I'LL DO the recency average multiple times - until there's ONE value left
            for example: if recency is 3
            then truncated recency would be 2, then 1
            so that's two "shorthand" growths
            but if recency is 5
            then truncated recency would be 4, 3, 2, then 1
            and that makes 4 additional growths. but this would actually be detrimental if the large growth happened only on the last frame of the X frames we're recording. coz then most of the lower growths will overtake the average.
            
            okay then - how about I go for the LAST 2 recency values?
            as opposed to whatever the recency is -1, i look at the last 2 recency values.
            
            yeah I think that would work, as that would seriously check for the growth over the last two frames, each time, even if the recency itself is fairly large. if recency looks over the last, say, 5 values, and the biggest growth happens in the last 1 or 2 values, the truncated recency, which always looks at the last 2 values, will always capture that large growth. if the growth happens over the last 5 values, then both will capture the same level of growth, so to say
            """
            # return average recent sizes
            return (size / self.recency), (sm_size / (len(trunc_rec_list)))
        else:
            return 0., 0.
    
    def average_size(self):
        # measures average across memory
        # avoid division by zero
        if len(self.mem_list) > 1:
            size = 0.
            # no use for absoluteness if i'm measuring average size
            for val in self.mem_list:
                size += val
            # return the the size average
            return size / self.mem_len
        else:
            return 0.
    
    def store_val(self, value):
        # stores value in memory, and clears memory if exceeding desired size
        self.mem_list.append(value)
        if len(self.mem_list) > self.mem_len:
            len_dif = len(self.mem_list) - self.mem_len
            # delete the oldest entries in the memory list X times, where X is by how much the current memory lenght differs from the desireable memory length
            '''for d in range(len_dif):
                del self.mem_list[0]'''
            del self.mem_list[0]
    
    def check_growth(self, avg_total, avg_recent1, avg_recent2):
        if avg_total > 0.:
            avg_growth1 = avg_recent1 / avg_total
            avg_growth2 = avg_recent2 / avg_total
            # return average between average growths
            # this is just a smoothing measure, as my bounding box i am measuring fluctuates wildly in size
            # and this would allow for a smoother growth get
            return (avg_growth1 + avg_growth2) / 2
        else:
            return 0.

    def get_delta(self, value):
        self.store_val(value)
        # total average size across all stored memory
        avg = self.average_size()
        # average size across recent frames (recency)
        rec1, rec2 = self.recent_size()
        # check for growth between recent and average
        growth = self.check_growth(avg, rec1, rec2)
        # return the growth
        '''print()
        print(avg)
        print(rec1, rec2)
        print()
        print(growth)'''
        return growth, avg