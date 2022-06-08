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

#create 3D array of particle positions over whole trajectory (N_frames,N_particles,3)
#positions = np.empty([len(traj),traj[0].particles.N,3])
positionslist = list()
positionslist[0] = traj[0].particles.position[:]
for i in range(0,len(traj)-1):
    positionslist.append(traj[i].particles.position[:])

positions = np.array(positionslist)
msd.compute(positions,reset=False)

print('msd[0:10]',msd.msd[0:11])
print('msd[0:10]',msd.msd[344388:344399])

traj.close()