class Packet:

    def __init__(self, time_stamp, source, destination):
        self.__time_stamp = time_stamp
        self.__source = source
        self.__destination = destination
        self.__type = ''

    def getTimeStamp(self):
        # get packet time stamp
        return self.__time_stamp

    def getSource(self):
        # get packet source
        return self.__source

    def getDestination(self):
        # get packet destination
        return self.__destination
    
    def getType(self):
        return self.__type

class RouteRequest(Packet):
    
    def __init__(self):
        self.__type = 'RouteRequest'
        
        
class RouteReply(Packet):
    
    def __init__(self):
        self.__type = 'RouteReply'
