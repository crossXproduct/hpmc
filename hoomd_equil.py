# TITLE: hoomd_equil.py
# AUTHOR: E. Aaron
# MODIFIED: 2022-06-22
# BRIEF: equilibrates a HOOMD-blue system that has been initialized via hoomd_init.py, continuation enabled

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

#Admin
s_eq = int(sys.argv[1]) #number of MC trials to run
write_interval = int(sys.argv[2]) #number of MC trials between file writes
chunks = int(sys.argv[3]) #number of equal chunks to break run into (chunks exceeding walltime will not be performed and state will be saved for continuation)
restart = bool(sys.argv[4])
run_block = s_eq/write_interval/chunks #number of steps to run in a chunk
WALLTIME_LIMIT = 7*24*3600 #OSC walltime limit in seconds
starttime = timeit.default_timer()

#RUN
#Set up simulation object
gpu = hoomd.device.GPU()
sim = hoomd.Simulation(device=gpu,seed=random_seed)
mc = hoomd.hpmc.integrate.Sphere(nselect=1)
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc
mc.d['sphere1'] = 0.06952022426028356 #step size optimized for phi=0.59
mc.d['sphere2'] = 0.06952022426028356

# Import initial condition
if restart==True: #if continuing incomplete run, start from intermediate state last saved
    sim.create_state_from_gsd(filename=job.fn('restart.gsd'))

else:
    sim.create_state_from_gsd(filename="compressed.gsd") #otherwise start from last completed step
    restart==False
#print("Timestep: ",sim.timestep)

# Set up trajectory writer
gsd_writer = hoomd.write.GSD(filename='equilibrated.gsd',mode='ab',trigger=hoomd.trigger.Periodic(write_interval),unwrap_full=True)
sim.operations.writers.append(gsd_writer)

# Run sim in chunks until about to exceed walltime limit
try:
    while sim.timestep <= s_eq:
        sim.run(min(run_block,s_eq-sim.timestep))
        if (sim.device.communicator.walltime + sim.walltime >= WALLTIME_LIMIT): break
finally: #if can't complete full run, save intermediate state to GSD file for continuation
    hoomd.write.GSD.write(state=sim.state,mode='wb',filename="restart.gsd")
    walltime = sim.device.communicator.walltime
    #print(f'run ended on step {sim.timestep} 'f'after {walltime} seconds')
    print(restart)

stoptime = timeit.default_timer()

#print("Timestep: ",sim.timestep)
#print("acceptance fraction: ",mc.translate_moves[0]/sum(mc.translate_moves))
#print("step size max ",mc.d['sphere1'],mc.d['sphere2'])
#print("elapsed 'time' (attempted moves): ",sum(mc.translate_moves)/int(N_particles))
#print('Run time: ',stoptime-starttime)