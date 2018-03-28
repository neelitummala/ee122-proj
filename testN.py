from Grid import *

def testN(N):
    c = []
    for i in range(N):
        g = Grid(100)
        c.append(g.isSingleSwarm())
    return c
