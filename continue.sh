#!/bin/bash

#initialize
echo "Initializing System..."
CONTINUE=False
RESTART=$(sbatch init.sh CONTINUE)
while[$RESTART -eq "True"];
do
CONTINUE=$(sbatch init.sh RESTART)
RESTART=CONTINUE
done
#equilibrate
echo "Equilibrating System..."
CONTINUE=False
RESTART=$(sbatch equil.sh CONTINUE)
while[$RESTART -eq "True"];
do
CONTINUE=$(sbatch equil.sh RESTART)
RESTART=CONTINUE
done
#run
echo "Running Simulation..."
CONTINUE=False
RESTART=$(sbatch equil.sh CONTINUE)
while[$RESTART -eq "True"];
do
CONTINUE=$(sbatch equil.sh RESTART)
RESTART=CONTINUE
done