import itertools
import math
import numpy as np
import copy
import hoomd
import gsd.hoomd
import os
import sys
import timeit
import random

N_particles = int(sys.argv[1]) #use an even number
t_sim = int(sys.argv[2]) # = 4.2e6 for 0.58
volume_fraction = np.double(sys.argv[3])
writing_interval = np.int(sys.argv[4])

starttime = timeit.default_timer()
random_seed = int(random.randrange(0,65535))

#Set up simulation
cpu = hoomd.device.CPU()
sim = hoomd.Simulation(device=cpu,seed=random_seed)
mc = hoomd.hpmc.integrate.Sphere(nselect=1)
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc

# Import initial condition
sim.timestep=0 #timestep automatically accumulates over runs unless reset. Must be reset BEFORE setting a sim state.
sim.create_state_from_gsd(filename="equilibrated.gsd")

# Set up trajectory writer
dcd_writer = hoomd.write.DCD(filename='trajectory.dcd',
                             trigger=hoomd.trigger.Periodic(writing_interval),
                             mode='xb')
sim.operations.writers.append(dcd_writer)

# Set sim step size
mc.d['sphere1'] = 0.06952022426028356 #optimized for phi=0.59
mc.d['sphere2'] = 0.06952022426028356

# Run sim
starttime = timeit.default_timer()
sim.run(t_sim)
stoptime = timeit.default_timer()
print("acceptance fraction: ",mc.translate_moves[0]/sum(mc.translate_moves))
print("step size max ",mc.d['sphere1'],mc.d['sphere2'])
print("elapsed 'time' (attempted moves): ",sum(mc.translate_moves)/int(N_particles))

print('Run time: ',stoptime-starttime)