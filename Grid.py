from Point import *
from Node import *

import random
import numpy as np

class Grid:
    
    def __init__(self, size):
        # creates a square grid of dimensions size x size
        # grid is a 2D numpy array
        
        self.__gridsize = size
        self.__grid = np.zeros((size,size), dtype=Node)
        
    # TODO: complete this fn
    def populate(self, swarm_size, seed=None):
        # populates the grid with a swarm of size swarm_size
        return None
        
    # TODO: need to generate n points without repeat
    def getRandomCoordinates(self, n, seed):
        x = np.zeros(n)
        y = np.zeros(n)
        
        random.seed(seed)
        
        for i in range(n):
            x[i] = random.randrange(self.__gridsize)
        
        return x