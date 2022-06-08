#include <cstdlib>
#include <gsd.h>
#include <cmath>
#include <vector>

using namespace std;


/** Write a function to read & return basic info about the GSD trajectory (gsd_info)
 * input: filename
 * DURING SIMULATION, WRITE A SEPERATE FILE WITH RUN INFO
 * num of particles (chunk = particles/N)
 * num of snapshots/frames (use function gsd_get_nframes)
 * num of steps between frames (need to input num of iterations to find)
 *
**/
//Write a function to read in a single particle's position at a given time (gsd_read)