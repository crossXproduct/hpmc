#!/bin/bash
#SBATCH --account=PHS0243
#SBATCH --time=7-00:00:00
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --mail-type=BEGIN,END,FAIL

#IMPORTANT: this template is meant to be used only by the continue.sh "driver" script for submitting continuous runs.
read;
cp $SLURM_SUBMIT_DIR/equil.in $TMPDIR
"$REPLY" >> equil.in
cp /fs/project/PHS0243/crossproduct/simulations/hoomd_equil.py $TMPDIR
module load miniconda3
source activate sims
CONTINUE=$(python3 hoomd_equil.py < equil.in)
if[$CONTINUE -eq "True"]; then
    cp restart.gsd $SLURM_SUBMIT_DIR
else
    cp equilibrated.gsd $SLURM_SUBMIT_DIR
fi
