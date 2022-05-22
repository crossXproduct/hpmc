import hoomd
import math
import numpy
import gsd.hoomd

#set up simulation from saved initial state
cpu = hoomd.device.CPU()
sim = hoomd.Simulation(device=cpu, seed=20)

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
sim.create_state_from_gsd(filename='lattice.gsd')

#save initial snapshot
initial_snapshot = sim.state.get_snapshot()

#run sim to randomize positions
sim.run(10e3) #arg is number of timesteps (or trials?)

#can query integrator properties to see their updated values
#calculate acceptance ratios of translation and rotation trials:
print(mc.translate_moves[0] / sum(mc.translate_moves)) #translate_moves stores accepted and rejected moves as (#accepted,#rejected)
#show overlapping particle pairs (none in final configuration):
print(mc.overlaps)

#save final snapshot
final_snapshot = sim.state.get_snapshot()

#can also query snapshot properties (position & orientation)
print(initial_snapshot.particles.position[0:4])
print(final_snapshot.particles.position[0:4])

#save fully randomized configuration to file
hoomd.write.GSD.write(state=sim.state, mode='xb', filename='random.gsd')
