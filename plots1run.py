import numpy as np
import matplotlib.pyplot as plt

TIME,MSD,FO, FSX,FSY,FSZ = np.loadtxt("output.dat",delimiter=',',unpack=True,dtype=np.double)

plt.scatter(TIME,MSD)
plt.yscale("log")
plt.xscale("log")
#plt.xlim(left=0.1)
#plt.ylim(bottom=0.1)
plt.title("Mean squared displacement")
plt.xlabel("mc steps")
plt.ylabel("msd")
plt.savefig("msd.png")
plt.clf()

plt.scatter(TIME,FO)
#plt.yscale("log")
plt.xscale("log")
plt.title("overlap function")
plt.xlabel("mc steps")
plt.ylabel("f_o")
plt.savefig("fo.png")
plt.clf()
