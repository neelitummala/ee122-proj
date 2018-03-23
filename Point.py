import math

class Point:
    
    def __init__(self, x, y):
        # x and y are integers
        self.__x = x
        self.__y = y
        
    def getX(self):
        return self.__x
    
    def getY(self):
        return self.__y
    
    def distanceToPoint(self, other_point):
        dx = self.__x - other_point.getX()
        dy = self.__y - other_point.getY()
        return math.hypot(dx, dy)
        
    