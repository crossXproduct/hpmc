#!/bin/bash

#initialize
echo "Initializing System..."
CONTINUE=False
RESTART=$(sbatch init.sh CONTINUE | awk 'NR==2{print $NF}')
echo $RESTART
while[$RESTART -eq "True"];
do
CONTINUE=$(sbatch init.sh RESTART | awk 'NR==2{print $NF}')
RESTART=CONTINUE
done
#equilibrate
echo "Equilibrating System..."
CONTINUE=False
RESTART=$(sbatch equil.sh CONTINUE | awk 'NR==2{print $NF}')
while[$RESTART -eq "True"];
do
CONTINUE=$(sbatch equil.sh RESTART | awk 'NR==2{print $NF}')
RESTART=CONTINUE
done
#run
echo "Running Simulation..."
CONTINUE=False
RESTART=$(sbatch equil.sh CONTINUE | awk 'NR==2{print $NF}')
while[$RESTART -eq "True"];
do
CONTINUE=$(sbatch equil.sh RESTART | awk 'NR==2{print $NF}')
RESTART=CONTINUE
done