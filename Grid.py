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
        self.populate(size, 0)
        
        
    # TODO: defined as average number of immediately adjacent neighbors that each node
    #       in the swarm can communicate with
    def measureSparsity(self):
        return None
    
    # generates a list of neighbors for each Node in the grid
    def findNeighbors(self):
        allNeighbors = []
        return None
    
    # populates the grid with a swarm of size swarm_size
    def populate(self, swarm_size, seed=None):
        randomCoordinates = self.getRandomCoordinates(swarm_size, seed)
        
        assert len(randomCoordinates) == swarm_size # sanity check
        
        for i in range(swarm_size):
            c = randomCoordinates.pop()
            n = Node(i, c)
            self.__grid[c.getX(), c.getY()] = n
        
        return None
        
    # returns a list of n unique Points
    def getRandomCoordinates(self, n, seed):
        points = []
        
		# seed RNG seed
        random.seed(seed)
        
        for _ in range(n):
            x = random.randrange(self.__gridsize)
            y = random.randrange(self.__gridsize)
            p = Point(x,y)
            
            # used to prevent repeats
            while(p in points):
                x = random.randrange(self.__gridsize)
                y = random.randrange(self.__gridsize)
                p = Point(x,y)
            
            points.append(p)
            
        return points