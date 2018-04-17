# File for running simulation

import numpy as np
import copy

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
        
        while not aodv.isFinished():
            run()
            
        print('Finished')
        
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
    
    def __init__(self, source, target, numNodes, timeout=10, retry=3):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__retry = retry # number of times node should try to re-transmit a packet
        self.__queues = QueueHolder(numNodes)
        self.__finished = False
        self.__destinationReached = False
        self.__lastTimeout = 0 # time at which the last timeout occurred
        beginDiscover(0)
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source)
        self.__queues[self.__source].addToBuffer(packet)
        
    def step(self, timeSlot, grid, neighbors, transmissions):
        # if it has been longer than timeout time slots, put a discovery packet back in the source node's queue
        if timeSlot - self.__lastTimeout > self.__timeout:
            beginDiscover(timeSlot)
            self.__lastTimeout = timeSlot
            
        for node in transmissions:
            if self.__queues[node].getBufferLength: # if queue is not empty, send packet out to neighbors
                neighbors = self.neighbors[node]
                packet = self.__queues[node].pullFromBuffer()
                sent = False
                for neighbor in neighbors:
                    if packet.getType() = 'RouteRequest':
                        if neighbor == self.__target and not self.__destinationReached: # so we don't send out multiple replies
                            self.__destinationReached = True
                            reply = RouteReply(timeSlot, neighbor, self.__source, packet.getPath()[::-1])
                            self.__queues[neighbor].addToBuffer(reply)
                        else:
                            newPacket = copy.deepcopy(packet)
                            if neighbor not in packet.getPath():
                                newPacket.addToPath(neighbor)
                                self.__queues[neighbor].addToBuffer(newPacket)
                        sent = True
                    if packet.getType() = 'RouteReply':
                        if neighbor == packet.getDestination(): # done with simulation
                            self.__finished = True
                            return
                        elif neighbor == packet.getPath[1]: # the neighbor is the next in the backwards path
                            if packet.getRetransmits() < self._retry: 
                                packet.setPath(packet.getPath()[1:])
                                self.__queues[neighbor].addToBuffer(packet)
                                sent = True
                            break
                if not sent:
                    packet.retransmit()
                    self.__queues[node].pushToFront(packet)
                        
    def getQueues(self):
        return self.__queues
                    
    def isFinished(self):
        return self.__finished
            