from collections import deque
import numpy as np

class QueueHolder:
    
    def __init__(self, numNodes):
        self.__numNodes = numNodes
        self.__queueHolder = {}
        self.populateQueues()
        
    def populateQueues(self):
        for node in np.arange(self.__numNodes):
            self.__queueHolder[node] = PacketQueue(node)    
    
    def getQueueHolder(self):
        return self.__queueHolder
    
    def getQueue(self, node):
        # convert back to string
        return self.__queueHolder[node]

class PacketQueue:
    
    def __init__(self, node, bufferLimit=10):
        self.__node = node
        self.__bufferLimit = bufferLimit # anything added if the queue is full will be dropped
        self.__buffer = deque(maxlen=self.__bufferLimit) # two-sided queue
    
    def getNode(self):
        return self.__node
    
    def getBufferLimit(self):
        return self.__bufferLimit
    
    def getBuffer(self):
        return self.__buffer
    
    def pushToBack(self, packet):
        self.__buffer.append(packet)
        
    def pushToFront(self, packet):
        self.__buffer.appendleft(packet)
        
    def pullFromBuffer(self):
        if not len(self.__buffer):
            return None
        return self.__buffer.pop()
    
    def getBufferLength(self):
        return len(self.__buffer)
