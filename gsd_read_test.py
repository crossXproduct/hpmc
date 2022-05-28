import math
import numpy as np
import hoomd
import gsd.hoomd
import sys

path = string(sys.argv[1])
traj = gsd.hoomd.open(path)

print('frames: ',len(traj))
print('first snapshot: ',traj[0].particles.position[0:10])

traj.close()