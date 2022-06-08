import itertools
import math
import numpy as np
import copy
import hoomd
import gsd.hoomd
import os
import sys
import timeit

t_sim = int(sys.argv[1])
dtsave = int(sys.argv[2])

starttime = timeit.default_timer()
#EQUILIBRATE
# Initialize sim
cpu = hoomd.device.CPU()
sim = hoomd.Simulation(device=cpu,seed=20)
mc = hoomd.hpmc.integrate.Sphere(nselect=1)
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc

# Import initial condition
sim.timestep=0 #timestep automatically accumulates over runs unless reset. Must be reset BEFORE setting a sim state.
sim.create_state_from_gsd(filename='compressed.gsd')
snapshot = gsd.hoomd.Snapshot()

# Set up trajectory writer
gsd_writer = hoomd.write.GSD(filename='trajectory.gsd',
                             trigger=hoomd.trigger.Periodic(period=dtsave),
                             mode='xb')
sim.operations.writers.append(gsd_writer)

# Tune sim step size
tune = hoomd.hpmc.tune.MoveSize.scale_solver(
    moves=['d'],
    target=0.2,
    trigger=hoomd.trigger.And([
        hoomd.trigger.Periodic(dtsave),
        hoomd.trigger.Before(sim.timestep + 5000) #what does this line do?
    ]))
sim.operations.tuners.append(tune)
sim.run(5000)
print("acceptance fraction: ",mc.translate_moves[0]/sum(mc.translate_moves))
print("elapsed 'time' (attempted moves): ",sum(mc.translate_moves)/int(snapshot.particles.N))
print(sim.timestep) #compare translate_moves with timestep to check
# Check tuning
sim.run(100)
translate_moves = mc.translate_moves
print("acceptance fraction: ",mc.translate_moves[0]/sum(mc.translate_moves))
print("elapsed 'time' (attempted moves): ",sum(mc.translate_moves)/int(N_particles))

# Run simulation
sim.run(t_sim)

stoptime = timeit.default_timer()
print('run time: ',stoptime-starttime)


#DONE! Now on to analysis...