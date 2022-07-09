#TITLE: init1.py
#MODIFIED: 22-05-23
#DESCRIPTION: Set up and run a simulation with 4 particles and volume fraction 0.57.

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
s_eq = int(sys.argv[2]) # = 4.2e6 for 0.58
s_run = int(sys.argv[3])
volume_fraction = np.double(sys.argv[4])
writing_interval = int(sys.argv[5])
#fill in more modifiable vars here

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

gpu = hoomd.device.GPU()

if gpu.communicator.rank == 0:
    init()

#RANDOMIZE
# Initialize sim
random_seed = int(random.randrange(0,65535))
sim = hoomd.Simulation(device=gpu,seed=random_seed)
mc = hoomd.hpmc.integrate.Sphere(nselect=1) #nselect is # of trial moves per timestep. Flenner uses 1.
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc
# Import initial condition
sim.create_state_from_gsd(filename='lattice.gsd')

initial_snapshot = sim.state.get_snapshot()
sim.run(10e3)
acceptance_ratio = mc.translate_moves[0] / sum(mc.translate_moves)
overlaps = mc.overlaps
if gpu.communicator.rank == 0:
    print(acceptance_ratio)
    print(overlaps)
final_snapshot = sim.state.get_snapshot()
if ((initial_snapshot.communicator.rank == 0) and (final_snapshot.communicator.rank == 0)):
    print(initial_snapshot.particles.position[0:4])
    print(final_snapshot.particles.position[0:4])

#f = os.system("touch random.gsd")
hoomd.write.GSD.write(state=sim.state, mode='xb', filename='random.gsd')


#COMPRESS
random_seed = int(random.randrange(0,65535))
sim = hoomd.Simulation(device=gpu, seed=random_seed)
sim.create_state_from_gsd(filename='random.gsd')

# Calculate initial volume fraction
V_particle1 = 4.0/3.0*math.pi*(mc.shape['sphere1']['diameter']/2)**3
V_particle2 = 4.0/3.0*math.pi*(mc.shape['sphere2']['diameter']/2)**3
initial_volume_fraction = (sim.state.N_particles / 2 * (V_particle1 + V_particle2) / sim.state.box.volume)
if gpu.communicator.rank == 0:
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
if gpu.communicator.rank == 0:
    print(sim.timestep)
if not compress.complete:
    raise RuntimeError("Compression failed to complete")
sphere1 = mc.d['sphere1']
sphere2 = mc.d['sphere2']
if gpu.communicator.rank == 0:
    print(sphere1)
    print(sphere2)

# Write compressed state to file
hoomd.write.GSD.write(state=sim.state, mode='xb', filename='compressed.gsd')
snapshot = sim.state.get_snapshot()
if snapshot.communicator.rank == 0:
    print(snapshot.particles.position[0:4])
inittime = timeit.default_timer() - starttime
if gpu.communicator.rank == 0:
    print('Setup time: ',inittime)

#EQUILIBRATE
# Initialize sim
random_seed = int(random.randrange(0,65535))
sim = hoomd.Simulation(device=gpu,seed=random_seed)
mc = hoomd.hpmc.integrate.Sphere(nselect=1)
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc

# Import initial condition
sim.timestep=0 #timestep automatically accumulates over runs unless reset. Must be reset BEFORE setting a sim state.
sim.create_state_from_gsd(filename='compressed.gsd')

# Set up trajectory writer
gsd_writer = hoomd.write.GSD(filename='equilibrated.gsd',trigger=hoomd.trigger.Periodic(writing_interval))
sim.operations.writers.append(gsd_writer)

# Set sim step size
mc.d['sphere1'] = 0.06952022426028356
mc.d['sphere2'] = 0.06952022426028356

# Run equilibration
sim.run(s_eq)
equiltime = timeit.default_timer() - inittime - starttime
equilsteps = sim.timestep
rate = equilsteps/equiltime #number of mc steps performed per second
acceptance_fraction = mc.translate_moves[0]/sum(mc.translate_moves)
sphere1 = mc.d['sphere1']
sphere2 = mc.d['sphere2']
attempted_moves = sum(mc.translate_moves)/int(N_particles)
if gpu.communicator.rank == 0:
    print("acceptance fraction: ",acceptance_fraction)
    print("step size max ",sphere1,sphere2)
    print("attempted moves: ",attempted_moves)
    print('Equilibration time: ',equiltime)

#RUN
#Set up simulation
random_seed = int(random.randrange(0,65535))
sim = hoomd.Simulation(device=gpu,seed=random_seed)
mc = hoomd.hpmc.integrate.Sphere(nselect=1)
mc.shape['sphere1'] = dict(diameter=1.0)
mc.shape['sphere2'] = dict(diameter=1.4)
sim.operations.integrator = mc
# Import initial condition
sim.timestep=0 #timestep automatically accumulates over runs unless reset. Must be reset BEFORE setting a sim state.
sim.create_state_from_gsd(filename="equilibrated.gsd")
# Set up trajectory writer
dcd_writer = hoomd.write.DCD(filename='trajectory.dcd', trigger=hoomd.trigger.Periodic(writing_interval),unwrap_full=True)
sim.operations.writers.append(dcd_writer)
# Set sim step size
mc.d['sphere1'] = 0.06952022426028356 #optimized for phi=0.59
mc.d['sphere2'] = 0.06952022426028356

# Run sim
sim.run(s_run)
stoptime = timeit.default_timer()

acceptance_fraction = mc.translate_moves[0]/sum(mc.translate_moves)
sphere1 = mc.d['sphere1']
sphere2 = mc.d['sphere2']
attempted_moves = sum(mc.translate_moves)/int(N_particles)
if gpu.communicator.rank == 0:
    print("acceptance fraction: ",acceptance_fraction)
    print("step size max ",sphere1,sphere2)
    print("elapsed 'time' (attempted moves): ",attempted_moves)
    print("Production time: ",stoptime-equiltime-inittime-starttime)
    print('Run time: ',stoptime-starttime)

#DONE! Now on to analysis...
