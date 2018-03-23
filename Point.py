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
        
    def __str__(self):
        return "(" + str(self.__x) + "," + str(self.__y) + ")"
        
    def __repr__(self):
        return "Point(" + str(self.__x) + "," + str(self.__y) + ")"