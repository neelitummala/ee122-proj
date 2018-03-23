import math

class Point:
    
    def __init__(self, x, y):
        # x and y are integers
        self.x = x
        self.y = y
    
    def distanceToPoint(self, other_point):
        dx = self.x - other_point.x