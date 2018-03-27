from Point import *
from Node import *

import random, math
import numpy as np

class Grid:
    
    # arbitrary definition of Rx/Tx reachable radius
    __radioRadius = 5
    
    def __init__(self, size):
        # creates a square grid of dimensions size x size
        # grid is a 2D numpy array
        # unpopulated points in the Grid denoted by 0
        
        self.__gridsize = size
        self.__grid = np.zeros((size,size), dtype=Node)
        self.__devices = []
        self.__allNeighbors = {}
        
        self.populate(size, 0)
        self.findNeighbors()
        
        self.__sparsity = self.measureSparsity()
        
        
    # TODO: defined as average number of immediately adjacent neighbors that each node
    #       in the swarm can communicate with
    def measureSparsity(self):
        sum = 0
        neighborLists = self.__allNeighbors.values()
        for nl in neighborLists:
            sum += len(nl)
        
        return sum / len(neighborLists)
        
    def getSparsity(self):
        return self.__sparsity
    
    # generates a list of neighbors for each Node in the grid
    def findNeighbors(self):
        
        # helper function for fast localized neighbor search
        # returns [upperLeftX, upperLeftY, lowerRightX, lowerRightY]
        def getRadiusCorners(point):
            x = point.getX()
            y = point.getY()
            ulx = (x - self.__radioRadius)
            uly = (y  - self.__radioRadius)
            lrx = (x + self.__radioRadius)
            lry = (y + self.__radioRadius)
            if ulx < 0:
                ulx = 0
            if uly < 0:
                uly = 0
            if lrx > (self.__gridsize - 1):
                lrx = (self.__gridsize - 1)
            if lry > (self.__gridsize - 1):
                lry = (self.__gridsize - 1)
            return [ulx, uly, lrx, lry]
            
        for d in self.__devices:
            neighbors = []
            ulx, uly, lrx, lry = getRadiusCorners(d.getCoordinate())
            for x in range(ulx,lrx+1):
                for y in range(uly,lry+1):
                    n = self.__grid[x,y]
                    if (type(n) == Node) and (n != d) and (n.distanceToNode(d) < self.__radioRadius):
                        neighbors.append(n)
                        
            self.__allNeighbors[d] = neighbors
                        
        return None
    
    def getNeighborsDict(self):
        return self.__allNeighbors
    
    def getGrid(self):
        return self.__grid
    
    # populates the grid with a swarm of size swarm_size
    def populate(self, swarm_size, seed=None):
        randomCoordinates = self.getRandomCoordinates(swarm_size, seed)
        
        assert len(randomCoordinates) == swarm_size # sanity check
        
        for i in range(swarm_size):
            c = randomCoordinates.pop()
            n = Node(i, c)
            self.__grid[c.getX(), c.getY()] = n
            self.__devices.append(n)
        
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
        
    def __str__(self):
        numDevices = len(self.__devices)
        zpcount = 0
        blank = "-"
        while(numDevices > 0):
            blank += "-"
            zpcount += 1
            numDevices = int(numDevices / 10)
            
        render = ""
        for x in range(self.__gridsize):
            for y in range(self.__gridsize):
                # x,y index ordering is reversed here to
                # account for numpy matrix ordering
                s = self.__grid[y,x]
                if s == 0:
                    render += blank
                else:
                    render += s.renderView(zpcount)
                render += " "
            render += "\n"
            
        return render
                
                
                
                
                
                
                
                