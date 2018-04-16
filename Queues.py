import queue

class QueueHolder:
    
    def __init__(self, numNodes):
        self.__numNodes = numNodes
        self.__queueHolder = {}
        self.populateQueues()
        
    def populateQueues(self):
        for node in numNodes:
            self.__queueHolder[node] = PacketQueue(node)    
    
    def getQueueHolder(self):
        return self.__queueHolder()

class PacketQueue:
    
    def __init__(self, node, bufferLimit=5):
        self.__node = node
        self.__bufferLimit = bufferLimit
        self.__buffer = queue.Queue(maxsize=self.__bufferSize) 
    
    def getNode(self):
        return self.__node
    
    def getBufferLimit(self):
        return self.__bufferLimit
    
    def getBuffer(self):
        return self.__buffer
    
    def addToBuffer(self, packet):
        self.__buffer.put(packet)
        
    def pullFromBuffer(self):
        if self.__buffer.empty():
            return None
        return self.__buffer.get()
    
    def getBufferLength(self):
        return len(self.__buffer)
