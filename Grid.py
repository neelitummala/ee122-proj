from Point import *
from Node import *
import numpy as np

class Grid:
    
    def __init__(self, size):
        # creates a square grid of dimensions size x size
        # grid is a 2D numpy array
        
        self.__size = size
        self.__grid = np.zeros((size,size), Node)