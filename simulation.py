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
        self.olsr.chooseMPR(self.grid, self.numNodes, self.neighbors) # choose multi-point relays for OLSR simulation
        self.custom = CustomSimulation(self.source, self.target, self.numNodes)

        # run through the simulations: OLSR, AODV, CUSTOM until they are all done
        while (not self.olsr.isFinished() or not self.aodv.isFinished()) or not self.custom.isFinished() and (self.timeSlot < self.maxTimeslots):
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
        arr =  [self.aodv.returnTimeslots(), self.aodv.returnOverhead(), self.aodv.returnQueueUsage()]
        arr.append(self.olsr.returnTimeslots())
        arr.append(self.olsr.returnOverhead())
        arr.append(self.olsr.returnQueueUsage())
        arr.append(self.custom.returnTimeslots())
        arr.append(self.custom.returnOverhead())
        arr.append(self.custom.returnQueueUsage())
        return arr

    def mutate(self):
        # mutates grid and updates everything every timeslot
        # mutates every 10 time slots and updates MPRs every 100
        if self.timeSlot % 10 == 0 and self.timeSlot != 0:
            self.nodeMovement = self.grid.mutate() # mutate the swarm
            self.custom.updateGraphNums(self.nodeMovement)
            self.neighbors = getNeighbors(self.grid.getNeighborsDict()) # update neighbors dictionary
            if self.timeSlot % 100 == 0:
                self.olsr.chooseMPR(self.grid, self.numNodes, self.neighbors) # update multi-point relays for OLSR
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
        self.__queueLength = 0
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue. This happens at the beginning and when we reach timeout
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source) 
        self.__queues.getQueue(self.__source).pushToBack(packet) # add RREQ to the source queue
        self.__received[self.__source] = timeSlot # record the timestamp of the packet
        
    def step(self, timeSlot, grid, neighborsDict, transmissions):
        # if it has been longer than timeout time slots, put a RREQ packet back in the source node's queue
        if timeSlot - self.__lastTimeout > self.__timeout: # if timeout occurs, source should send out another RREQ
            self.beginDiscover(timeSlot)
            self.__lastTimeout = timeSlot
        
        # record queue length
        num = 0
        for node in range(self.__numNodes):
            num += self.__queues.getQueue(node).getBufferLength()
        self.__queueLength += (num / self.__numNodes)       

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

    def returnQueueUsage(self):
        return ((self.__queueLength / self.__totalTimeslots) / 10) * 100
    
class OLSRSimulation:
    
    def __init__(self, source, target, numNodes, timeout=100, retry=5, linkUpdate=50):
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
        for node in range(numNodes):
            self.__MPR[node] = []
            self.__routingTables[node] = [-1]*self.__numNodes
        self.__numMPR = 0
        self.beginDiscover(0)
        
        # measurement variables for comparisons
        self.__totalTimeslots = 0
        self.__totalOverhead = 0
        self.__queueLength = 0
        
    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue. This happens at the beginning and when we reach timeout
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source)
        self.__queues.getQueue(self.__source).pushToBack(packet)
        self.__received[self.__source] = timeSlot # record the timestamp of the packet

    def refreshState(self, timeSlot):
        # if it's time to update the link, put a link state message back in all the queues
        for node in range(self.__numNodes):
            packet = LinkState(timeSlot, node)
            self.__queues.getQueue(node).pushToBack(packet)
        
    def chooseMPR(self, grid, numNodes, neighborsDict):
        # gather all two-hop neighbors
        for node in range(numNodes):
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
        if (timeSlot - self.__lastLinkUpdate > self.__linkUpdate) or timeSlot == 0:
            self.refreshState(timeSlot)
            self.__lastLinkUpdate = timeSlot

        # record queue length
        num = 0
        for node in range(self.__numNodes):
            num += self.__queues.getQueue(node).getBufferLength()
        self.__queueLength += (num / self.__numNodes) 

        for node in transmissions:
            if self.__queues.getQueue(node).getBufferLength(): # if queue is not empty, send packet out to MPRs
                MPRs = self.__MPR[node]
                packet = self.__queues.getQueue(node).pullFromBuffer() 
                sent = False # if the packet doesn't get sent this whole loop, we need to retransmit it
                for MPR in MPRs: # packets are only forwarded to MPRs
                    if MPR in neighborsDict[node]: # since we don't update MPRs at every time step, we should make sure they are still neighbors
                        table = self.__routingTables[MPR] # routing table for the MPR
                        if packet.getType() == 'RouteRequest':
                            # if the destination is in the neighbor's routing table and it's up to date, then there is a route and we've finished
                            if (packet.getDestination() == MPR) or ((table[packet.getDestination()] > 0) and (table[packet.getDestination()] + self.__linkUpdate >= timeSlot)):
                                self.__finished = True
                                self.__totalTimeslots = timeSlot
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
                                sent = True
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

    def returnQueueUsage(self):
        return ((self.__queueLength / self.__totalTimeslots) / 10) * 100
    
class CustomSimulation:
    
    def __init__(self, source, target, numNodes, timeout=10, degree=1):
        self.__source = source
        self.__target = target
        self.__numNodes = numNodes
        self.__timeout = timeout # time before source node resends a discovery packets
        self.__degree = degree # number of neighbors to try and send to
        self.__queues = QueueHolder(numNodes)
        self.__finished = False
        self.__lastTimeout = 0 # time at which the last timeout occurred
        self.__received = [-1]*self.__numNodes # array of timestamps that record what RREQ packet a node has received (so it doesn't retransmit it)
        self.__replyReceived = [-1]*self.__numNodes # whether a node has gotten a route reply or not so it doesnt send it again
        self.__graphNums = [0]*self.__numNodes # keeps track of how many times a node has moved
        self.__brokenPath = False # if the path on the way back is broken, we have to broadcast the packet
        self.__destinationReached = False # if the target node has been reached with an RREQ

        # measurement variables for comparisons
        self.__totalTimeslots = 0
        self.__totalOverhead = 0
        self.__queueLength = 0

    def step(self, timeSlot, grid, neighborsDict, transmissions, nodeMovement):
        # if it has been longer than timeout time slots, put a RREQ packet back in the source node's queue
        if timeSlot - self.__lastTimeout > self.__timeout: # if timeout occurs, source should send out another RREQ
            self.beginDiscover(timeSlot)
            self.__lastTimeout = timeSlot

        # record queue length
        num = 0
        for node in range(self.__numNodes):
            num += self.__queues.getQueue(node).getBufferLength()
        self.__queueLength += (num / self.__numNodes) 
        
        for node in transmissions:
            if self.__queues.getQueue(node).getBufferLength(): # if queue is not empty, send packet out to neighbors
                neighbors = self.pickNeighbors(copy.deepcopy(neighborsDict[node])) # order neighbors by graph number: smallest to largest
                packet = self.__queues.getQueue(node).pullFromBuffer() 
                sent = 0 # WAS THE ROUTE REPLY SENT DEGREE NUMBER OF TIMES?
                requestSent = 0 # WAS AN RREQ SENT DEGREE NUMBER OF TIMES?
                for neighbor in neighbors:
                    if (packet.getType() == 'RouteRequest') and (requestSent < self.__degree) : # we only want to forward the RREQ to degree # of nodes
                        if neighbor == self.__target and not self.__destinationReached: # so we don't send out multiple replies
                            self.__destinationReached = True
                            reply = RouteReply(timeSlot, self.__target, self.__source, packet.getPath()[::-1])
                            self.__queues.getQueue(neighbor).pushToBack(reply)
                            requestSent += 1
                            self.__totalOverhead += 1
                        elif (self.__received[neighbor] < packet.getTimeStamp()): # if we havent received this request before
                            newPacket = copy.deepcopy(packet) # copy the packet so we don't have pointers
                            newPacket.addToPath(neighbor)
                            self.__queues.getQueue(neighbor).pushToBack(newPacket)
                            self.__received[neighbor] = packet.getTimeStamp()
                            requestSent += 1
                            self.__totalOverhead += 1
                    elif packet.getType() == 'RouteReply':
                        if neighbor == packet.getDestination(): # FINISHED SIMULATION
                            self.__finished = True
                            self.__totalTimeslots = timeSlot
                            return
                        elif self.__brokenPath:
                            if (self.__replyReceived[neighbor] < packet.getTimeStamp()) and (sent < self.__degree):
                                newPacket = copy.deepcopy(packet)
                                self.__queues.getQueue(neighbor).pushToBack(newPacket)
                                self.__replyReceived[neighbor] = packet.getTimeStamp()
                                sent += 1
                                self.__totalOverhead += 1
                        elif neighbor == packet.getPath()[0]: # the neighbor is the next in the backwards path and the path hasn't broken yet
                            packet.setPath(packet.getPath()[1:])
                            self.__queues.getQueue(neighbor).pushToBack(packet)
                            sent += 1
                            self.__totalOverhead += 1
                            break
                if (packet.getType() == 'RouteReply') and (sent == 0) and (not self.__brokenPath): # if this is a reply and the path has broken, we need to broadcast the reply
                    self.__brokenPath = True
                    for n in neighbors: # broadcast packet to all neighbors
                        temp = copy.deepcopy(packet)
                        self.__replyReceived[n] = temp.getTimeStamp()
                        self.__queues.getQueue(n).pushToFront(temp)
        
    def isFinished(self):
        return self.__finished

    def updateGraphNums(self, nodeMovement):
        self.__graphNums += nodeMovement

    def pickNeighbors(self, neighbors):
        neighborGraphNums = [self.__graphNums[i] for i in neighbors]
        neighbors = [x for _,x in sorted(zip(neighborGraphNums, neighbors))]
        return neighbors

    def beginDiscover(self, timeSlot):
        # put route request packet into source's queue. This happens at the beginning and when we reach timeout
        packet = RouteRequest(timeSlot, self.__source, self.__target)
        packet.addToPath(self.__source)
        self.__queues.getQueue(self.__source).pushToBack(packet)
        self.__received[self.__source] = timeSlot # record the timestamp of the packet

    def returnOverhead(self):
        return self.__totalOverhead
    
    def returnTimeslots(self):
        return self.__totalTimeslots

    def returnQueueUsage(self):
        return ((self.__queueLength / self.__totalTimeslots) / 10) * 100

        
