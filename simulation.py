# File for running simulation

import numpy as np

from Grid import *
from Packet import *
from Queues import *

def get_p(grid, node):
    """
        Probability of successful transmission for a given node.

        Parameters
        ----------
        grid: Grid object
            the grid of the swarm
        node: int
            node we need the probability of transmission for

        Returns
        -------
        :int
            probability of successful transmission for a given node
    """
    # TODO: change probability of transmission based on number of neighbors
    # for now return a constant
    return 0.5

def transmissions(grid, numNodes):
    """
        Which nodes transmit in the current timeslot.

        Parameters
        ----------
        grid: Grid object
            the grid of the swarm

        Returns
        -------
        :obj:list
            list of nodes that will transmit in the current timeslot
    """
    transmissions = []
    for node in np.arange(numNodes):
        p = get_p(grid, node)
        if np.random.choice(2, p=[1-p, p]):
            transmissions.append(node)
    return transmissions

class Simulation:
    """
        Runs various simulations.
    """
    def __init__(self, grid):
        self.grid = grid
        self.neighbors = grid.getNeighborsDict()
        self.numNodes = len(self.neighbors)
        self.timeSlot = 0
   
        # randomly choose the source and destination nodes
        choice = np.random.choice(numNodes, 2, replace=False)
        self.source = choice[0]
        self.target = choice[1]
        
        aodv = AODVSimulation(self.source, self.target, self.numNodes)
        
        while not aodv.finished():
            run()
        
    def run(self):
        send = transmissions(self.grid, self.numNodes)
        if not aodv.finished():
            aodv.step()
        mutate()
            
    def mutate(self):
        # mutates grid and updates everything every timeslot
        # TODO: incorporate Hall's mutate function
        # TODO: update neighbors
        self.timeSlot += 1
        return
        
class AODVSimulation:
    
    def __init__(self, source, target, numNodes):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__queues = QueueHolder(numNodes)
        self.__finished = False
        beginDiscover(0)
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue
        self.__queues[self.__source].addToBuffer(RouteRequest(timeSlot, self.__source, self.__target))
        
    def step(self, timeSlot, grid, neighbors, transmissions):
        for node in transmissions:
            if self.__queues[node].getBufferLength: # if queue is not empty, send packet out to neighbors
                neighbors = self.neighbors[node]
                for neighbor in neighbors:
                    self.__queues[neighbor].addToBuffer(RouteRequest(timeSlot, self.__source, self.__target))

    def getQueues(self):
        return self.__queues
                    
    def isFinished(self):
        return self.__finished
            