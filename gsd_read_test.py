import math
import numpy as np
import hoomd
import gsd.hoomd
import sys

path = str(sys.argv[1])
traj = gsd.hoomd.open(path)

print('frames: ',len(traj))
print('particles: ',traj[0].size())
print('first snapshot: ',traj[0].particles.position[0:10])

traj.close()