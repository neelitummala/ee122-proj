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

def getNeighbors(neighborsDict):
    """
        Reformat the neighbors dictionary for a grid.

        Parameters
        ----------
        neighborsDict: dict
            dictionary of neighbors for each node in the grid

        Returns
        -------
        :dict
            reformatted dictionary of neighbors in the grid
    """
    newDict = {}
        nodes = []
        for key in neighborsDict.keys():
            keyID = key.getID()
            nodes.append(keyID)
            neighbors = neighborsDict[key]
            newList = []
            for n in neighbors:
                newList.append(n.getID())
            newDict[keyID] = newList
    return newDict

class Simulation:
    """
        Runs various simulations: AODV, OLSR, CUSTOM
    """
    def __init__(self, grid, maxTimeslots=5000):
        self.grid = grid
        self.neighbors = getNeighbors(self.grid.getNeighborsDict()) 
        self.numNodes = len(self.neighbors)
        self.maxTimeslots = maxTimeslots # simulation gets cut off after this so we don't infinite loop
        self.timeSlot = 0
           
        # randomly choose the source and destination nodes
        choice = np.random.choice(self.numNodes, 2, replace=False)
        self.source = choice[0]
        self.target = choice[1]

        # dictionary that tells us whether a node has moved since the last time step
        # instantiate with all zeros
        self.nodeMovement = {}
        for node in range(self.numNodes):
            self.nodeMovement[node] = 0

        # instantiate different simulations: AODV, OLSR, CUSTOM
        self.aodv = AODVSimulation(self.source, self.target, self.numNodes)
        self.olsr = OLSRSimulation(self.source, self.target, self.numNodes)
        self.olsr.chooseMPR(self.grid, self.nodes, self.neighbors) # choose multi-point relays for OLSR simulation
        self.custom = CustomSimulation(self.source, self.target, self.numNodes)

        # run through the simulations: OLSR, AODV, CUSTOM until they are all done
        while (not self.olsr.isFinished() or not self.aodv.isFinished()) and (self.timeSlot < self.maxTimeslots):
            send = transmissions(self.grid, self.numNodes) # choose nodes that will successfully transmit in this timeslot
            if not self.aodv.isFinished():
                self.aodv.step(self.timeSlot, self.grid, self.neighbors, send)
            if not self.olsr.isFinished():
                self.olsr.step(self.timeSlot, self.grid, self.neighbors, send)
            if not self.custom.isFinished():
                self.custom.step(self.timeSlot, self.grid, self.neighbors, send, self.nodeMovement)
            self.mutate()
            
    def end(self):
        # return results
        return [self.aodv.returnTimeslots(), self.aodv.returnOverhead(), self.olsr.returnTimeslots(), self.olsr.returnOverhead()]

    def mutate(self):
        # mutates grid and updates everything every timeslot
        self.nodeMovement = self.grid.mutate() # mutate the swarm
        self.neighbors = getNeighbors(self.grid.getNeighborsDict()) # update neighbors dictionary
        self.olsr.chooseMPR(self.grid, self.nodes, self.neighbors) # update multi-point relays for OLSR
        self.timeSlot += 1
        return
        
class AODVSimulation:
    
    def __init__(self, source, target, numNodes, timeout=100, retry=5):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__retry = retry # number of times node should try to re-transmit a packet
        self.__queues = QueueHolder(numNodes) # queue for each node
        self.__finished = False # whether the simulation is done yet or not
        self.__destinationReached = False # if the target node has been reached with an RREQ
        self.__lastTimeout = 0 # time at which the last timeout occurred
        self.__received = [None]*self.__numNodes # array of timestamps that record what RREQ packet a node has received (so it doesn't retransmit it)
        self.beginDiscover(0) # put RREQ packet in the source's queue
        
        # measurement variables for comparisons
        self.__totalTimeslots = 0
        self.__totalOverhead = 0
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue. This happens at the beginning and when we reach timeout
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source) 
        self.__queues.getQueue(self.__source).pushToBack(packet) # add RREQ to the source queue
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
                if not sent: # if the packet hasn't been taken out of the queue and sent, we need to retransmit
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
    
    def __init__(self, source, target, numNodes, timeout=100, retry=5, linkUpdate=20):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__retry = retry # number of times node should try to re-transmit a packet
        self.__linkUpdate = linkUpdate # how often the link state information is sent out
        self.__queues = QueueHolder(numNodes)
        self.__finished = False
        self.__lastTimeout = 0 # time at which the last timeout occurred
        self.__lastLinkUpdate = 0 # the last time the link state messages were passed around
        self.__received = [None]*self.__numNodes # array of timestamps that record what RREQ packet a node has received (so it doesn't retransmit it)
        self.__MPR = {} # MPRS for each node
        self.__routingTables = {} # for each node, has a list of the timestamps for when the node received a link state message for that node
        for node in np.arange(numNodes):
            self.__MPR[node] = []
            self.__routingTables[node] = [0]*self.__numNodes
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

    def refreshState(self, timeSlot):
        # if it's time to update the link, put a link state message back in all the queues
        for node in range(self.__numNodes):
            packet = LinkState(timeSlot, node)
            self.queues.getQueue(node).pushToBack(packet)
        
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
        
        # if it has been longer than linkUpdate time slots, all the nodes should send out link states again
        if timeSlot - self.__lastLinkUpdate > self.__linkUpdate:
            self.refreshState(timeSlot)
            self.__lastLinkUpdate = timeSlot

        for node in transmissions:
            if self.__queues.getQueue(node).getBufferLength(): # if queue is not empty, send packet out to MPRs
                MPRs = self.__MPR[node]
                packet = self.__queues.getQueue(node).pullFromBuffer() 
                sent = False # if the packet doesn't get sent this whole loop, we need to retransmit it
                for MPR in MPRs: # packets are only forwarded to MPRs
                    if packet.getType() == 'RouteRequest':
                        table = self.__routingTables[MPR]
                        # if the destination is in the neighbor's routing table and it's up to date, then there is a route and we've finished
                        if (packet.getDestination() == MPR) or ((table[packet.getDestination()] > 0) and (table[packet.getDestination()] + self.__linkUpdate >= timeSlot)):
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
                        if table[packet.getSource()] < packet.getTimeStamp(): # only send the packet if it's new and hasn't been seen before
                            table[packet.getSource()] = packet.getTimeStamp()
                            newPacket = copy.deepcopy(packet) # copy the packet so we don't have pointers
                            newPacket.addToPath(MPR)
                            self.__queues.getQueue(MPR).pushToBack(newPacket)
                            self.__totalOverhead += 1
                if not sent:
                    packet.retransmit()
                    self.__queues.getQueue(node).pushToFront(packet)        
        
    def returnOverhead(self):
        return self.__totalOverhead
    
    def returnTimeslots(self):
        return self.__totalTimeslots
    
    def isFinished(self):
        return self.__finished
    
    def getMPR(self):
        return self.__MPR
    
class CustomSimulation:
    
    def __init__(self, source, target, numNodes, timeout=10, retry=5):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__retry = retry # number of times node should try to re-transmit a packet
        self.__queues = QueueHolder(numNodes)
        self.__finished = False
        self.__lastTimeout = 0 # time at which the last timeout occurred
        self.__received = [None]*self.__numNodes # array of timestamps that record what RREQ packet a node has received (so it doesn't retransmit it)

    def step(self, timeSlot, grid, neighborsDict, transmissions, nodeMovement):
        return
        
    def isFinished(self):
        return self.__finished
        