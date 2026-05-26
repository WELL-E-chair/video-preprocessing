#!/bin/bash

#SBATCH --job-name=preprocess-daymonth
#SBATCH --account=def-PIname
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=64
#SBATCH --mem=249G
#SBATCH --time=72:00:00
#SBATCH --mail-user=youremail@address.com  # Email 
#SBATCH --mail-type=ALL                # Notify START, END, FAIL
#SBATCH --output=%x_%j.out

module load python/3.10

cd $SLURM_TMPDIR
mkdir tmp

cp /home/path/to/projects/preprocessing/src/preprocessing-daily.py $SLURM_TMPDIR/

# Virtual environment
python -m venv .venv
source .venv/bin/activate
pip install --no-index numpy pandas


# Run script
python preprocessing-daily.py \
    --input_data "/path/to/preprocessing/video/input/project_name/" \
    --local "/path/to/preprocessing/video/input/" \
    --meta_data "" \
    --target_date "DDMMMYYYY" \
    --experiment "project_name" \
    --output_data  "/path/to/preprocessing/video/input/processed/" 
