import freud
import gsd.hoomd
import scipy
import numpy as np
import sys

path = str(sys.argv[1])
traj = gsd.hoomd.open(path,'rb')

print('frames: ',len(traj))
print('particles: ',len(traj[0].particles.position))
print('first snapshot: ',traj[0].particles.position[0:10])

print(traj[0].configuration.box,traj[1].configuration.box)
msd = freud.msd.MSD(traj[0].configuration.box)

msd.compute(traj[:].particles.position[:])

print('msd[0:10]',msd.msd[0:11])
print('msd[0:10]',msd.msd[344388:344399])

traj.close()