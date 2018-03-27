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
        
    def setCoordinate(self, new_coordinate):
        self.__coordinate = new_coordinate
        return
        
    def distanceToNode(self, other_node):
        return self.__coordinate.distanceToPoint(other_node.getCoordinate())
        
    def __str__(self):
        return "N" + str(self.__id) + " at " + str(self.__coordinate)
        
    def __repr__(self):
        return "N" + str(self.__id)