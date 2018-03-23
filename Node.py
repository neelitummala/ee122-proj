class Node:
	
    def __init__(self, id, coordinate):
        # id is an integer
        # coordinate is a Point
        self.__id = id
        self.__coordinate = coordinate
        
    def getID(self):
        return self.__id
        
    def getCoordinate(self):
        return self.__coordinate
        
    def distanceToNode(self, other_node):
        return self.__coordinate.distanceToPoint(other_node.getCoordinate())