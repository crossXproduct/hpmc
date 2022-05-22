import copy
import math
import hoomd

#initialize simulation from randomized initial state
cpu = hoomd.device.CPU()
sim = hoomd.Simulation(device=cpu, seed=20)
sim.create_state_from_gsd(filename='random.gsd')

#calculate volume fraction
#find volume of 1 particle (octahedron in this case)
a = math.sqrt(2)/2
V_particle = 1/3*math.sqrt(2)*a**3
#volume fraction
initial_volume_fraction = (sim.state.N_particles*V_particle / sim.state.box.volume)
print(initial_volume_fraction)

#set up Integrator to move particle positions for compression
mc = hoomd.hpmc.integrate.ConvexPolyhedron()
mc.shape['octahedron'] = dict(vertices=[
    (-0.5, 0, 0),
    (0.5, 0, 0),
    (0, -0.5, 0),
    (0, 0.5, 0),
    (0, 0, -0.5),
    (0, 0, 0.5),
])
sim.operations.integrator = mc

#set up Updater (QuickCompress) to compress system, and assign to Simulation
initial_box = sim.state.box
final_box = hoomd.Box.from_box(initial_box)
final_volume_fraction = 0.57
final_box.volume = sim.state.N_particles * V_particle / final_volume_fraction
compress = hoomd.hpmc.update.QuickCompress(trigger=hoomd.trigger.Periodic(10),
                                           target_box=final_box)
sim.operations.updaters.append(compress) #can have multiple updaters, but only 1 integrator

#set up a tuner (MoveSize) to optimize the MC trial step size
periodic = hoomd.trigger.Periodic(10)
tune = hoomd.hpmc.tune.MoveSize.scale_solver(moves=['a', 'd'], 
                                             target=0.2, #acceptance ratio 20% is usually optimal
                                             trigger=periodic,
                                             max_translation_move=0.2,
                                             max_rotation_move=0.2)
sim.operations.tuners.append(tune)

#run the simulation with updater and tuner until desired volume fraction is met
while not compress.complete and sim.timestep < 1e6: #limit timesteps to avoid possible infinities (possible compression may never complete)
    sim.run(1000)
print(sim.timestep)
if not compress.complete: #check to see if compression completed
    raise RuntimeError("Compression failed to complete")

#check adjusted move sizes
print(mc.a['octahedron'])
print(mc.d['octahedron'])

#save final compressed state
hoomd.write.GSD.write(state=sim.state, mode='xb', filename='compressed.gsd')
