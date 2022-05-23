#TITLE: init1.py
#MODIFIED: 22-05-22
#DESCRIPTION: initialize simulation with 100 particles and volume fractions 0.5, 0.55, and 0.58

import itertools
import math
import numpy as np
import hoomd
import gsd.hoomd
import signac
import os

statepoint = dict(N_particles=100, volume_fraction=0.58, seed=20)
project = signac.init_project(name="glass-exchange-times")
os.system("cat signac.rc")

job = project.open_job(statepoint)
job.statepoint
job.document

def init(job):
    K = math.ceil(job.statepoint.N_particles**(1/3))
    spacing = 1.2
    L = K*spacing
    x = numpy.linspace(-L/2,L/2,K,endpoint=False)
    position = list(itertools.product(x,repeat=3))
    position = position[0:job.statepoint.N_particles]

    snapshot = gsd.hoomd.Snapshot()
    snapshot.particles.typeid = [0,1]*job.statepoint.N_particles*0.5
    snapshot.particles.types = ['sphere','sphere']
    snapshot.configuration.box = [L,L,L,0,0,0]

    with gsd.hoomd.open(name=job.fn('lattice.gsd'),mode='xb') as f:
        f.append(snapshot)

    job.document['initialized'] = True

for volume_fraction in [0.5,0.55,0.58]:
    statepoint = dict(N_particles=100, volume_fraction=volume_fraction, seed=20)
    job = project.open_job(statepoint)
    job.init()
    init(job)