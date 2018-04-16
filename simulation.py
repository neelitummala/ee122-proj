# File for running simulation

import numpy as np
import Grid 

def get_p(grid, node):
    """
        Probability of successful transmission for a given node.

        Parameters
        ----------
        grid: Grid object
            the grid of the swarm
        node: int
            node we need the probability of transmission for

        Returns
        -------
        :int
            probability of successful transmission for a given node
    """
    # TODO: change probability of transmission based on number of neighbors
    # for now return a constant
    return 0.5

def transmissions(grid):
    """
        Which nodes transmit in the current timeslot.

        Parameters
        ----------
        grid: Grid object
            the grid of the swarm

        Returns
        -------
        :obj:list
            list of nodes that will transmit in the current timeslot
    """
    numNodes = grid.__idCount
    transmissions = []
    for node in np.arange(numNodes):
        p = get_p(grid, node)
        if np.random.choice(2, p=[1-p, p]):
            transmissions.append(node)
    return transmissions

def run_simulation():
    """
        Which nodes transmit in the current timeslot.

        Parameters
        ----------
        grid: Grid object
            the grid of the swarm

        Returns
        -------
        :obj:list
            list of nodes that will transmit in the current timeslot
    """
    grid = Grid(10)
    
    return

if __name__ == "__main__":
	test_grid = Grid(10)
	print(test_grid)