# TITLE: hoomd_equil.py
# AUTHOR: E. Aaron
# MODIFIED: 2022-06-22
# BRIEF: initializes, randomizes, and compresses a HOOMD-blue system and saves state to 'compressed.gsd'

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
volume_fraction = np.double(sys.argv[2])
s_eq = int(sys.argv[3]) #number of MC trials to run
s_run = int(sys.argv[4]) #number of MC trials to run
write_interval = int(sys.argv[5]) #number of MC trials between file writes
equil_chunks = int(sys.argv[6]) #number of equal chunks to break equilibration into (chunks exceeding walltime will not be performed and state will be saved for continuation)
run_chunks = int(sys.argv[7])
walltime = int(sys.argv[8]) #walltime allotted for full simulation in batch script
restart_init = bool(sys.argv[9])
restart_random = bool(sys.argv[10])
restart_compress = bool(sys.argv[11])
restart_equil = bool(sys.argv[12])
restart_run = bool(sys.argv[13])


equil_block = s_eq/write_interval/equil_chunks #number of steps to run in a chunk
run_block = s_run/write_interval/run_chunks #number of steps to run in a chunk
random_seed = int(random.randrange(0,65535))
starttime = timeit.default_timer()

#INITIALIZE
def init():
    K = math.ceil(N_particles**(1/3))
    spacing = 2
    L = K*spacing
    x = np.linspace(-L/2,L/2,K,endpoint=False)
    position = list(itertools.product(x,repeat=3))
    position = position[0:N_particles]
    print(position[0:4])

    snapshot = gsd.hoomd.Snapshot()
    snapshot.particles.N = N_particles
    snapshot.particles.position = position
    snapshot.particles.typeid = [0]*math.floor(N_particles/2) + [1]*math.floor(N_particles/2)
    print(math.floor(N_particles/2))
    print(snapshot.particles.typeid[0:4])
    snapshot.particles.types = ['sphere1','sphere2']
    snapshot.configuration.box = [L,L,L,0,0,0]
    print(snapshot.particles.types)
    with gsd.hoomd.open(name='lattice.gsd',mode='xb') as f:
        f.append(snapshot)

#RANDOMIZE
# Initialize sim
def randomize():
    gpu = hoomd.device.GPU()
    sim = hoomd.Simulation(device=gpu,seed=random_seed)
    mc = hoomd.hpmc.integrate.Sphere(nselect=1) #nselect is # of trial moves per timestep. Flenner uses 1.
    mc.shape['sphere1'] = dict(diameter=1.0)
    mc.shape['sphere2'] = dict(diameter=1.4)
    sim.operations.integrator = mc
    # Import initial condition
    sim.create_state_from_gsd(filename='lattice.gsd')

    initial_snapshot = sim.state.get_snapshot()
    sim.run(10e3)
    print(mc.translate_moves[0] / sum(mc.translate_moves))
    print(mc.overlaps)
    final_snapshot = sim.state.get_snapshot()
    print(initial_snapshot.particles.position[0:4])
    print(final_snapshot.particles.position[0:4])

    #f = os.system("touch random.gsd")
    hoomd.write.GSD.write(state=sim.state, mode='xb', filename='random.gsd')

#COMPRESS
def compress():
    gpu = hoomd.device.GPU()
    sim = hoomd.Simulation(device=gpu, seed=random_seed)
    sim.create_state_from_gsd(filename='random.gsd')

    # Calculate initial volume fraction
    V_particle1 = 4.0/3.0*math.pi*(mc.shape['sphere1']['diameter']/2)**3
    V_particle2 = 4.0/3.0*math.pi*(mc.shape['sphere2']['diameter']/2)**3
    initial_volume_fraction = (sim.state.N_particles / 2 * (V_particle1 + V_particle2) / sim.state.box.volume)
    print(initial_volume_fraction)

    # Assign integrator
    mc = hoomd.hpmc.integrate.Sphere(nselect=1)
    mc.shape['sphere1'] = dict(diameter=1.0)
    mc.shape['sphere2'] = dict(diameter=1.4)
    sim.operations.integrator = mc

    # Create and assign compression updater (compress sys to desired volume fraction)
    initial_box = sim.state.box
    final_box = hoomd.Box.from_box(initial_box)
    final_volume_fraction = volume_fraction
    final_box.volume = sim.state.N_particles / 2 * (V_particle1 + V_particle2) / final_volume_fraction
    compress = hoomd.hpmc.update.QuickCompress(trigger=hoomd.trigger.Periodic(10), target_box=final_box)
    sim.operations.updaters.append(compress)

    # Set max step size
    mc.d['sphere1'] = 0.06952022426028356 #optimized for phi=0.59
    mc.d['sphere2'] = 0.06952022426028356

    # Run compression
    while not compress.complete and sim.timestep < 1e6:
        sim.run(1000)
    print(sim.timestep)
    if not compress.complete:
        raise RuntimeError("Compression failed to complete")
    print(mc.d['sphere1'])
    print(mc.d['sphere2'])

    # Write compressed state to file
    hoomd.write.GSD.write(state=sim.state, mode='xb', filename='compressed.gsd')
    print(sim.state.get_snapshot().particles.position[0:4])

setuptime = timeit.default_timer()
print("SETUP TIME=",setuptime)

#Run any init steps missing
if restart_init == True: init()
if restart_random == True: randomize()
if restart_compress == True: compress()

#EQUILIBRATE
#Set up simulation object
equilstart = timeit.default_timer()
gpu = hoomd.device.GPU()
sim = hoomd.Simulation(device=gpu,seed=random_seed)
mc = hoomd.hpmc.integrate.Sphere(nselect=1)
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc
mc.d['sphere1'] = 0.06952022426028356 #step size optimized for phi=0.59
mc.d['sphere2'] = 0.06952022426028356

# Import initial condition
if restart_equil==True: #if continuing incomplete run, start from intermediate state last saved
    sim.create_state_from_gsd(filename=job.fn('restart.gsd'))

else:
    sim.create_state_from_gsd(filename="compressed.gsd") #otherwise start from last completed step
    restart_equil==False
#print("Timestep: ",sim.timestep)

# Set up trajectory writer
gsd_writer = hoomd.write.GSD(filename='equilibrated.gsd',mode='ab',trigger=hoomd.trigger.Periodic(write_interval),unwrap_full=True)
sim.operations.writers.append(gsd_writer)

# Run sim in chunks until about to exceed walltime limit
try:
    while sim.timestep <= s_eq:
        sim.run(min(equil_block,s_eq-sim.timestep))
        current_time = timeit.default_timer() - starttime
        if (current_time + sim.walltime >= walltime): break
finally: #if can't complete full run, save intermediate state to GSD file for continuation
    hoomd.write.GSD.write(state=sim.state,mode='wb',filename="restart_equil.gsd")
    walltime = sim.device.communicator.walltime
    #print(f'run ended on step {sim.timestep} 'f'after {walltime} seconds')
    print("Restart equilibration? ",restart_equil)
equiltime = timeit.default_timer() - setuptime
print("EQUILIBRATION TIME=",equiltime)

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
if restart_run==True: #if continuing incomplete run, start from intermediate state last saved
    sim.create_state_from_gsd(filename=job.fn('restart_run.gsd'))

else:
    sim.create_state_from_gsd(filename="equilibrated.gsd") #otherwise start from last completed step
    restart_run==False
#print("Timestep: ",sim.timestep)

# Set up trajectory writer
dcd_writer = hoomd.write.DCD(filename='trajectory.dcd',overwrite=False,trigger=hoomd.trigger.Periodic(write_interval),unwrap_full=True)
sim.operations.writers.append(dcd_writer)

# Run sim in chunks until about to exceed walltime limit
try:
    while sim.timestep <= s_run:
        sim.run(min(run_block,s_run-sim.timestep))
        current_time = timeit.default_timer() - starttime
        if (current_time + sim.walltime >= walltime): break
finally: #if can't complete full run, save intermediate state to GSD file for continuation
    hoomd.write.GSD.write(state=sim.state,mode='wb',filename="restart.gsd")
    walltime = sim.device.communicator.walltime
    #print(f'run ended on step {sim.timestep} 'f'after {walltime} seconds')
    print("Restart run? ",restart_run)
stoptime = timeit.default_timer()
runtime = stoptime - equiltime
totaltime = stoptime - starttime
print("RUNTIME=",runtime)
print("TOTAL TIME=",totaltime)