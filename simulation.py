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
    return 0.3

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
    def __init__(self, grid, maxTimeslots=5000):
        self.grid = grid
        self.neighbors = grid.getNeighborsDict()
        self.maxTimeslots = maxTimeslots # simulation gets cut off after this so we don't infinite loop
        
        # instantiate neighbors in a better way (by just integers instead of nodes)
        newDict = {}
        self.nodes = []
        for key in self.neighbors.keys():
            keyID = key.getID()
            self.nodes.append(keyID)
            neighbors = self.neighbors[key]
            newList = []
            for n in neighbors:
                newList.append(n.getID())
            newDict[keyID] = newList
        self.neighbors = newDict
        
        self.numNodes = len(self.neighbors)
        self.timeSlot = 0
           
        # randomly choose the source and destination nodes
        choice = np.random.choice(self.numNodes, 2, replace=False)
        self.source = choice[0]
        self.target = choice[1]
        
        self.aodv = AODVSimulation(self.source, self.target, self.numNodes)
        self.olsr = OLSRSimulation(self.source, self.target, self.numNodes)
        self.olsr.chooseMPR(self.grid, self.nodes, self.neighbors)

        while (not self.olsr.isFinished() or not self.aodv.isFinished()) and (self.timeSlot < self.maxTimeslots):
            send = transmissions(self.grid, self.numNodes)
            if not self.aodv.isFinished():
                self.aodv.step(self.timeSlot, self.grid, self.neighbors, send)
            if not self.olsr.isFinished():
                self.olsr.step(self.timeSlot, self.grid, self.neighbors, send)
            self.mutate()
            

    def end(self):
        # return results
        return [self.aodv.returnTimeslots(), self.aodv.returnOverhead(), self.olsr.returnTimeslots(), self.olsr.returnOverhead()]

    def mutate(self):
        # mutates grid and updates everything every timeslot
        # TODO: incorporate Hall's mutate function
        # TODO: update neighbors
        # TODO: update MPRs for OLSR
        self.timeSlot += 1
        return
        
class AODVSimulation:
    
    def __init__(self, source, target, numNodes, timeout=100, retry=3):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__retry = retry # number of times node should try to re-transmit a packet
        self.__queues = QueueHolder(numNodes) # queue for each node
        self.__finished = False
        self.__destinationReached = False # if the target node has been reached with an RREQ
        self.__lastTimeout = 0 # time at which the last timeout occurred
        self.__received = [None]*self.__numNodes # array of timestamps that record what RREQ packet a node has received (so it doesn't retransmit it)
        self.beginDiscover(0)
        
        # measurement variables for comparisons
        self.__totalTimeslots = 0
        self.__totalOverhead = 0
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue. This happens at the beginning and when we reach timeout
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source)
        self.__queues.getQueue(self.__source).pushToBack(packet)
        self.__received[self.__source] = timeSlot # record the timestamp of the packet
        
    def step(self, timeSlot, grid, neighborsDict, transmissions):
        # if it has been longer than timeout time slots, put a discovery packet back in the source node's queue
        if timeSlot - self.__lastTimeout > self.__timeout: # if timeout occurs, source should send out another RREQ
            self.beginDiscover(timeSlot)
            self.__lastTimeout = timeSlot
            
        for node in transmissions:
            if self.__queues.getQueue(node).getBufferLength(): # if queue is not empty, send packet out to neighbors
                neighbors = neighborsDict[node]
                packet = self.__queues.getQueue(node).pullFromBuffer() 
                sent = False # if the packet doesn't get sent this whole loop, we need to retransmit it
                for neighbor in neighbors:
                    if packet.getType() == 'RouteRequest':
                        if neighbor == self.__target and not self.__destinationReached: # so we don't send out multiple replies
                            self.__destinationReached = True
                            reply = RouteReply(timeSlot, self.__target, self.__source, packet.getPath()[::-1])
                            self.__queues.getQueue(neighbor).pushToBack(reply)
                        elif (self.__received[neighbor] is None) or (self.__received[neighbor] < packet.getTimeStamp()):
                            # if we havent received this request before
                            newPacket = copy.deepcopy(packet) # copy the packet so we don't have pointers
                            newPacket.addToPath(neighbor)
                            self.__queues.getQueue(neighbor).pushToBack(newPacket)
                            self.__received[neighbor] = packet.getTimeStamp()
                        sent = True
                        self.__totalOverhead += 1
                    if packet.getType() == 'RouteReply':
                        if neighbor == packet.getDestination(): # done with simulation because the reply packet has reached the source
                            self.__finished = True
                            self.__totalTimeslots = timeSlot
                            print("AODV")
                            print("Total timeslots: "+str(self.__totalTimeslots))
                            print("Total overhead: "+str(self.__totalOverhead))
                            print("Finished")
                            return
                        elif neighbor == packet.getPath()[0]: # the neighbor is the next in the backwards path
                            if packet.getRetransmits() <= self.__retry: 
                                packet.setPath(packet.getPath()[1:])
                                self.__queues.getQueue(neighbor).pushToBack(packet)
                                sent = True
                                self.__totalOverhead += 1
                            break
                if not sent:
                    packet.retransmit()
                    self.__queues.getQueue(node).pushToFront(packet)
                        
    def getQueues(self):
        return self.__queues
                    
    def isFinished(self):
        return self.__finished
    
    def returnOverhead(self):
        return self.__totalOverhead
    
    def returnTimeslots(self):
        return self.__totalTimeslots
    
class OLSRSimulation:
    
    def __init__(self, source, target, numNodes, timeout=10, retry=3):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__retry = retry # number of times node should try to re-transmit a packet
        self.__queues = QueueHolder(numNodes)
        self.__finished = False
        self.__lastTimeout = 0 # time at which the last timeout occurred
        self.__received = [None]*self.__numNodes # array of timestamps that record what RREQ packet a node has received (so it doesn't retransmit it)
        self.__MPR = {}
        for node in np.arange(numNodes):
            self.__MPR[node] = []
        self.__routingTable = [0]*self.__numNodes
        self.__numMPR = 0
        self.beginDiscover(0)
        
        # measurement variables for comparisons
        self.__totalTimeslots = 0
        self.__totalOverhead = 0
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue. This happens at the beginning and when we reach timeout
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source)
        self.__queues.getQueue(self.__source).pushToBack(packet)
        self.__received[self.__source] = timeSlot # record the timestamp of the packet
        
        packet = LinkState(timeSlot, self.__target)
        packet.addToPath(self.__target)
        self.__queues.getQueue(self.__target).pushToBack(packet)
        
    def chooseMPR(self, grid, nodes, neighborsDict):
        # gather all two-hop neighbors
        for node in nodes:
            twoHopNeighbors = set()
            # set of MPRs needs to cover all two-hop neighbors of the node
            for neighbor in neighborsDict[node]:
                for twoHop in neighborsDict[neighbor]:
                    if twoHop != node and twoHop not in neighborsDict[node]: # not current node and not first-hop neighbor
                        twoHopNeighbors.add(twoHop)
            # now find MPRs
            shuffledNeighbors = copy.deepcopy(neighborsDict[node])
            np.random.shuffle(shuffledNeighbors)
            for neighbor in shuffledNeighbors:
                intersection = twoHopNeighbors & set(neighborsDict[neighbor])
                if len(intersection):
                    twoHopNeighbors = twoHopNeighbors - intersection
                    self.__MPR[node].append(neighbor)
                    self.__numMPR += 1
                    
    def step(self, timeSlot, grid, neighborsDict, transmissions):
        # if it has been longer than timeout time slots, put a discovery packet back in the source node's queue
        if timeSlot - self.__lastTimeout > self.__timeout: # if timeout occurs, source should send out another RREQ
            self.beginDiscover(timeSlot)
            self.__lastTimeout = timeSlot
            
        for node in transmissions:
            if self.__queues.getQueue(node).getBufferLength(): # if queue is not empty, send packet out to MPRs
                MPRs = self.__MPR[node]
                packet = self.__queues.getQueue(node).pullFromBuffer() 
                sent = False # if the packet doesn't get sent this whole loop, we need to retransmit it
                for MPR in MPRs:
                    if packet.getType() == 'RouteRequest':
                        # if the destination is in the neighbor's routing table, then there is a route and we've finished
                        if self.__routingTable[node] == 1:
                            self.__finished = True
                            self.__totalTimeslots = timeSlot
                            print("OLSR")
                            print("Total timeslots: "+str(self.__totalTimeslots))
                            print("Total overhead: "+str(self.__totalOverhead))
                            print("Finished")
                            return
                        elif (self.__received[MPR] is None) or (self.__received[MPR] < packet.getTimeStamp()):
                            # if we havent received this request before
                            newPacket = copy.deepcopy(packet) # copy the packet so we don't have pointers
                            newPacket.addToPath(MPR)
                            self.__queues.getQueue(MPR).pushToBack(newPacket)
                            self.__received[MPR] = packet.getTimeStamp()
                        sent = True
                        self.__totalOverhead += 1
                    if packet.getType() == 'LinkState':
                        self.__routingTable[node] = 1
                        newPacket = copy.deepcopy(packet) # copy the packet so we don't have pointers
                        newPacket.addToPath(MPR)
                        self.__queues.getQueue(MPR).pushToBack(newPacket)
                        self.__totalOverhead += 1
                if not sent:
                    packet.retransmit()
                    self.__queues.getQueue(node).pushToFront(packet)
        # add the packets being sent out as HELLO packets
        self.__totalOverhead += self.__numMPR*0.3 # times 0.3 because that is the probability of transmission
        
        
    def returnOverhead(self):
        return self.__totalOverhead
    
    def returnTimeslots(self):
        return self.__totalTimeslots
    
    def isFinished(self):
        return self.__finished
    
    def getMPR(self):
        return self.__MPR