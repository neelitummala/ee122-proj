class Packet:
    # super class for all packets
    
    def __init__(self, time_stamp, source, destination):
        self.__time_stamp = time_stamp # when the packet originated
        self.__source = source # the source
        self.__destination = destination # the target
        self.__retransmits = 0

    def getTimeStamp(self):
        # get packet time stamp
        return self.__time_stamp

    def getSource(self):
        # get packet source
        return self.__source

    def getDestination(self):
        # get packet destination
        return self.__destination
    
    def retransmit(self):
        # when the packet gets sent back into a queue, increment the number of times it has been re-transmitted.
        # this happens when a reverse path gets broken by movement of the swarm
        self.__retransmits += 1
    
    def getRetransmits(self):
        return self.__retransmits

class RouteRequest(Packet):
    # AODV route request packet 
    
    def __init__(self, time_stamp, source, destination):
        Packet.__init__(self, time_stamp, source, destination)
        self.__type = 'RouteRequest'
        self.__path = [] # path that the request has taken

    def getType(self):
        return self.__type
    
    def addToPath(self, node):
        self.__path.append(node)
        
    def getPath(self):
        return self.__path

class RouteReply(Packet):
    # AODV route reply packet
    
    def __init__(self, time_stamp, source, destination, path):
        Packet.__init__(self, time_stamp, source, destination)
        self.__type = 'RouteReply'
        self.__path = path # reverse path from target -> source

    def getType(self):
        return self.__type
    
    def setPath(self, path):
        self.__path = path
        
    def getPath(self):
        return self.__path

class LinkState():
    # OLSR link state packet
    def __init__(self, time_stamp, source):
        self.__type = 'LinkState'
        self.__timeStamp = time_stamp
        self.__source = source
        self.__retransmits = 0
        self.__path = []
        
    def getSource(self):
        return self.__source
    
    def getTimeStamp(self):
        return self.__timeStamp
    
    def getType(self):
        return self.__type
    
    def retransmit(self):
        # when the packet gets sent back into a queue, increment the number of times it has been re-transmitted.
        # this happens when a reverse path gets broken by movement of the swarm
        self.__retransmits += 1
    
    def getRetransmits(self):
        return self.__retransmits
    
    def addToPath(self, node):
        self.__path.append(node)
        
    def getPath(self):
        return self.__path