import math
import hoomd
import itertools
import numpy
import gsd.hoomd

##DEFINE SIMULATION & SIM INTEGRATOR
#Simulation ... the object containing all information about the simulation. Members:
#  state - the current configuration of the system
#  device - GPU or CPU
#  operations - a subclass containing integrators, updaters, and writers
cpu = hoomd.device.CPU() #declare Device first
sim = hoomd.Simulation(device=cpu, seed=1) #declare Simulation

#Integrator ... defines the operation performed by Simulation (hard particle MC in this case)
mc = hoomd.hpmc.integrate.ConvexPolyhedron()
mc.shape['octahedron'] = dict(vertices=[ #specify the shape of the object Integrator will act on
    (-0.5,0,0),
    (0.5,0,0),
    (0,-0.5,0),
    (0,0.5,0),
    (0,0,-0.5),
    (0,0,0.5)
])
#set other properties of Integrator:
mc.nselect = 2 #number of mc trials per timestep
mc.d['octahedron'] = 0.15 #upper bound on translation per trial
mc.a['octahedron'] = 0.2 #upper bound on rotation per trial (won't need rotations for spherical MC...)

#assign Integrator to Simulation:
sim.operations.integrator = mc


#INITIALIZE SYSTEM STATE
#number of particles to simulate
m = 4
n_p = 2*m**3
#define spacing and size of box (will use 3D box of length L)
spacing = 1.2
K = math.ceil(n_p**(1/3)) #number of particles per dimension (?)
L = K*spacing #length of box
#define the box and set initial positions
x = numpy.linspace(-L/2,L/2,K,endpoint=False) #box must be periodic
position = list(itertools.product(x,repeat=3)) #set positions (iterate once per dimension)
print(position[0:4]) #for demonstration
#restrict number of positions to n_p
position = position[0:n_p]
#set orientation vector
orientation = [(1,0,0,0)]*n_p #list multiplication duplicates the list


#STORE INITIAL STATE TO FILE
#gsd snapshot stores state
snapshot = gsd.hoomd.Snapshot()
snapshot.particles.N = n_p
snapshot.particles.position = position
snapshot.particles.orientation = orientation
#define particle types (this apparently is done for each particle individually)
snapshot.particles.typeid = [0] * n_p #using 0 as type id, there is only one
snapshot.particles.types = ['octahedron'] #type name is any string
#define box using gsd params (L_x,L_y,L_z,tilt_1,tilt_2,tilt_3)
snapshot.configuration.box = [L, L, L, 0, 0, 0]
#write snapshot to .gsd file
with gsd.hoomd.open(name='lattice.gsd', mode='xb') as f:
    f.append(snapshot)


#INITIALIZE SIMULATION
#use initial state file to initialize simulation:
sim.create_state_from_gsd(filename='lattice.gsd')
