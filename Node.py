import Point

class Node:
	
    def __init__(self, id, coordinate):
        # id is an integer
        # coordinate is a Point
        # using _ prefix on class variables means don't touch them except via class functions
        self._id = id
        self._coordinate = coordinate
        
    def getID(self):
        return self._id
        
    def getCoordinate(self):
        return self._coordinate
        
    def distanceToNode(self, other_node):
        return self._coordinate