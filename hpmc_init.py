#TITLE: init1.py
#MODIFIED: 22-05-23
#DESCRIPTION: Set up a simulation with the specified parameters.
##  ARGS:
##      N_particles (int)           number of particles
##      volume_fraction (np.double) packing fraction

import itertools
import math
import numpy as np
import copy
import hoomd
import gsd.hoomd
import os
import sys
import timeit

starttime = timeit.default_timer()

N_particles = int(sys.argv[1]) #use an even number
volume_fraction = np.double(sys.argv[2])
#fill in more modifiable vars here

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
init()


#RANDOMIZE
# Initialize sim
cpu = hoomd.device.CPU()
sim = hoomd.Simulation(device=cpu,seed=20)
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
cpu = hoomd.device.CPU()
sim = hoomd.Simulation(device=cpu, seed=20)
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

# Create and assign step size tuner (optimize MC step size for best performance)
periodic = hoomd.trigger.Periodic(10)

tune = hoomd.hpmc.tune.MoveSize.scale_solver(moves=['d'],
                                             target=0.2,
                                             trigger=periodic,
                                             max_translation_move=0.2,
                                            )
sim.operations.tuners.append(tune)


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

stoptime = timeit.default_timer()
print('run time: ',stoptime-starttime)