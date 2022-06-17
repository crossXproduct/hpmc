import numpy as np
import matplotlib.pyplot as plt
import os

path = input("Path to run folders: ")
name = os.path.basename(path)

TIME,Msd,Fo,Fsx,Fsy,Fsz = np.loadtxt(name + '/output_1k.dat',unpack=True,dtype=np.double,delimiter=',')
TVALS, MSD, MSD_ERR, FO, FO_ERR, FSX, FSX_ERR, FSY, FSY_ERR, FSZ, FSZ_ERR = np.loadtxt(path + '/averages_flenner_10k' + '.dat', delimiter=',', unpack=True)

#Plots
plt.errorbar(TVALS, MSD, yerr=MSD_ERR, fmt='', ecolor='black', barsabove=True, marker='o', color='green')
plt.scatter(TIME,Msd,marker='^',color='red')
plt.xlim(left=0)
plt.xscale('log')
plt.yscale('log')
plt.rcParams['xtick.top'] = plt.rcParams['xtick.labeltop'] = True
plt.legend(['HOOMD-blue','Flenner'])
plt.title('Mean Squared Displacement')
plt.xlabel('time (MC steps)')
plt.ylabel('msd (diameters)')
plt.savefig(path + "/msd_compare.png")
plt.clf()

plt.errorbar(TVALS, FO, yerr=FO_ERR, fmt='', ecolor='black', barsabove=True, marker='o', color='green')
plt.scatter(TIME,Fo,marker='^',color='red')
plt.xlim(left=0)
plt.xscale('log')
plt.rcParams['xtick.top'] = plt.rcParams['xtick.labeltop'] = True
plt.legend(['Flenner','HOOMD-blue'])
plt.title('Overlap Function')
plt.xlabel('time (MC steps)')
plt.ylabel('F_o')
plt.savefig(path + "/fo_compare.png")
plt.clf()

plt.errorbar(TVALS, FSX, yerr=FSX_ERR, fmt='', ecolor='black', barsabove=True, marker='o', color='red')
plt.errorbar(TVALS, FSY, yerr=FSY_ERR, fmt='', ecolor='black', barsabove=True, marker='o', color='green')
plt.errorbar(TVALS, FSZ, yerr=FSZ_ERR, fmt='', ecolor='black', barsabove=True, marker='o', color='blue')
plt.scatter(TIME,Fsx,marker='^',color='red')
plt.scatter(TIME,Fsy,marker='^',color='green')
plt.scatter(TIME,Fsz,marker='^',color='blue')
plt.xlim(left=0)
plt.xscale('log')
plt.rcParams['xtick.top'] = plt.rcParams['xtick.labeltop'] = True
plt.legend(['Flenner X','Flenner Y','Flenner Z','HOOMD-blue X','HOOMD-blue Y','HOOMD-blue Z'])
plt.title('Self-Intermediate Scattering Function')
plt.xlabel('t')
plt.ylabel('F_s')
plt.savefig(path + "/fs_compare.png")