# File for running simulation

import numpy as np

def create_timeslots(num_slots, num_nodes, prob):
	# num_slots is number of slots simulation should run for
	# num_nodes is number of nodes in the network
	# prob is array of probabilities of successful transmission for each node
	# returns an array of time slots with an array of the nodes transmitting in each slot

	time_slots = [[] for i in range(num_slots)]
	for node in np.arange(num_nodes):
		transmissions = np.random.choice(2, num_slots, p=[1-prob[node], prob[node]])
		for j in np.nonzero(transmissions)[0]:
			time_slots[j].append(node)

	return time_slots

if __name__ == "__main__":
	time_slots = create_timeslots(100, 5, [0.1, 0.2, 0.8, 0.9, 0.01])
	print(time_slots)