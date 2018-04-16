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
        Initializes variables for the simulation.
    """
    def __init__(self, grid):
        self.grid = grid
        self.numNodes = len(grid.getNeighborsDict())
   
    # randomly choose the source and destination nodes
        choice = np.random.choice(numNodes, 2, replace=False)
        self.source = choice[0]
        self.dest = choice[1]
        
    def runAODV(self):
        queues = QueueHolder(numNodes)
        pathFound = False # tells us whether the simulation should end or not
        timeSlot = 0
        
        while not pathFound:
            for node in transmissions(grid, numNodes):
                continue
        
        timeSlot += 1 # increment timeslot
