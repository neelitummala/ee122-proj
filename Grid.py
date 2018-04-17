# TODO:
# implement removeDevice()
# implement mutate()

from Point import *
from Node import *

import random, math
import numpy as np
from collections import deque

class Grid:
    
    # arbitrary definition of Rx/Tx reachable radius
    __radioRadius = 5
    
    def __init__(self, size, seed=None):
        # creates a square grid of dimensions size x size
        # grid is a 2D numpy array
        # unpopulated points in the Grid denoted by 0
        
        self.__gridsize = size
        self.__grid = np.zeros((size,size), dtype=Node)
        self.__devices = []
        self.__idCount = 0
        self.__allNeighbors = {}
        
        self.populate(int(size*size/5), seed) # guarantees that 1/5 of grid will be occupied
        self.findNeighbors()
        
        self.__sparsity = self.measureSparsity()
        
        
    # defined as average number of immediately adjacent neighbors that each node
    # in the swarm can communicate with
    def measureSparsity(self):
        sum = 0
        neighborLists = self.__allNeighbors.values()
        for nl in neighborLists:
            sum += len(nl)
        
        return sum / len(neighborLists)
        
    def getSparsity(self):
        return self.__sparsity
    
    # generates a list of neighbors for each Node in the grid
    # if singleDevice is None, will find neighbors for all devices
    # if singleDevice is not None, will only find neighbors for that device
    def findNeighbors(self, singleDevice=None):
        
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
        
        if singleDevice == None:
            for d in self.__devices:
                neighbors = []
                ulx, uly, lrx, lry = getRadiusCorners(d.getCoordinate())
                for x in range(ulx,lrx+1):
                    for y in range(uly,lry+1):
                        n = self.__grid[x,y]
                        if (type(n) == Node) and (n != d) and (n.distanceToNode(d) <= self.__radioRadius):
                            neighbors.append(n)
                            
                self.__allNeighbors[d] = neighbors
        else:
            d = singleDevice
            neighbors = []
            ulx, uly, lrx, lry = getRadiusCorners(d.getCoordinate())
            for x in range(ulx,lrx+1):
                for y in range(uly,lry+1):
                    n = self.__grid[x,y]
                    if (type(n) == Node) and (n != d) and (n.distanceToNode(d) <= self.__radioRadius):
                        neighbors.append(n)
                        
            self.__allNeighbors[d] = neighbors
                        
        return None
    
    def getNeighborsDict(self):
        return self.__allNeighbors
        
    def getNode(self, x, y):
        if type(self.__grid[x,y]) != Node:
            print("No Node found at " + str(Point(x, y)))
            return False
        else:
            return self.__grid[x,y]
    
    # mutates the entire swarm
    # 1. iterate through each device in Grid
    # 2. get rectangle surrounding device defined by mobility radius
    # 3. choose a place to move to randomly.
    # 4. make sure swarm is still contiguous. if not, redo #3
    # 5. if there are no possible places to move, pop device from fringe and re-add to back
    # 6. for any device, give up trying to move after 3 tries
    def mutate(self):
        fringe = deque([])
        # add all devices to fringe.
        for d in self.__devices:
            fringe.append([d, 0])
        # do the mutate
        while len(fringe) != 0:
            d = fringe.popleft()
            oldX = d.getCoordinate().getX()
            oldY = d.getCoordinate().getY()
            # TODO: finish this
    
    # moves device from one coordinate to another in Grid
    # 1. make sure device is in Grid
    # 2. make sure new location is empty
    # 3. make a copy of device's current neighbors
    # 4. set new grid location to node
    # 5. set current grid location to 0
    # 6. update node neighbors and new neighbors' neighbors
    # 7. update old neighbors' neighbors
    def moveDevice(self, currX, currY, newX, newY):
        if type(self.__grid[currX, currY]) != Node:
            print("No Node found at " + str(Point(currX, currY)))
            return False
        elif type(self.__grid[newX, newY]) == Node:
            print(str(Point(newX, newY)) + " is not empty")
            return False
        else:
            movingNode = self.__grid[currX, currY]
            oldNeighbors = self.__allNeighbors[movingNode]
            self.__grid[currX, currY] = 0
            movingNode.setCoordinate(Point(newX,newY))
            self.__grid[newX, newY] = movingNode
            self.findNeighbors(movingNode)
            for n in self.__allNeighbors[movingNode]:
                self.findNeighbors(n)
            for on in oldNeighbors:
                self.findNeighbors(on)
            
            return True
    
    # adds a new Device to Grid
    def addDevice(self, newNode):
        if (newNode in self.__devices):
            print("Node already in grid")
            return False
            
        newX = newNode.getCoordinate().getX()
        newY = newNode.getCoordinate().getY()
        if type(self.__grid[newX, newY]) == Node:
            print("Coordinate already occupied!")
            return False
        else:
            newNode.setID(self.__idCount)
            self.__idCount += 1
            self.__devices.append(Node)
            self.__grid[newX, newY] = newNode
            self.findNeighbors(newNode)
            # need to also update the neighbors list of all new neighbors
            for n in self.__allNeighbors[newNode]:
                self.findNeighbors(n)
            return True
        
    
    def getGrid(self):
        return self.__grid
    
    # populates the grid with a swarm of size swarm_size
    def populate(self, swarm_size, seed):
        randomCoordinates = self.getRandomCoordinates(swarm_size, seed)
        
        assert len(randomCoordinates) == swarm_size # sanity check
        
        for i in range(swarm_size):
            c = randomCoordinates.pop()
            n = Node(i, c)
            self.__grid[c.getX(), c.getY()] = n
            self.__devices.append(n)
            self.__idCount += 1
        
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
    
    # determines if all devices in grid are part of a single
    # contiguous swarm
    def isSingleSwarm(self):
        swarm = []
        fringe = []
        startNode = self.__devices[0]
        
        fringe.extend(self.__allNeighbors[startNode])
        
        while(len(fringe) > 0):
            n = fringe.pop()
            if n not in swarm:
                swarm.append(n)
                fringe.extend(self.__allNeighbors[n])
        
        return len(swarm) == len(self.__devices)
        
    def __str__(self):
        numDevices = self.__idCount
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
                
                
                
                
                
                
                
                