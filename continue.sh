#!/bin/bash

#initialize
echo "Initializing System..."
CONTINUE="False"
CONTINUE=$(sbatch init.sh < CONTINUE)
while[$CONTINUE -eq "True"];
do CONTINUE=$(sbatch init.sh < CONTINUE)
done
#equilibrate
echo "Equilibrating System..."
CONTINUE=$(sbatch equil.sh < CONTINUE)
while[$CONTINUE -eq "True"];
do
CONTINUE=$(sbatch equil.sh < CONTINUE)
done
#run
echo "Running Simulation..."
CONTINUE=$(sbatch equil.sh < CONTINUE)
while[$CONTINUE -eq "True"];
do
CONTINUE=$(sbatch equil.sh < CONTINUE)
done