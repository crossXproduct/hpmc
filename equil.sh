#!/bin/bash
#SBATCH --account=PHS0243
#SBATCH --time=7-00:00:00
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --mail-type=BEGIN,END,FAIL

#IMPORTANT: this template is meant to be used only by the continue.sh "driver" script for submitting continuous runs.
cp $SLURM_SUBMIT_DIR/equil.in $TMPDIR
cd /fs/project/PHS0243/crossproduct/simulations/
cp hoomd_equil.py $TMPDIR
cd $TMPDIR
module load miniconda3
source activate sims
python3 hoomd_equil.py 18150000 18150 10 False
cp restart.gsd $SLURM_SUBMIT_DIR
cp equilibrated.gsd $SLURM_SUBMIT_DIR