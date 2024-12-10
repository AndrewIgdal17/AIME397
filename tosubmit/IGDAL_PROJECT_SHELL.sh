#!/bin/bash
#SBATCH -J final_project           # Job name
#SBATCH -o final_project.o%j         # Output file (%j will be replaced with job ID)
#SBATCH -e final_project.e%j         # Error file
#SBATCH -p development              # Queue (partition) name
#SBATCH -N 1                        # Number of nodes
#SBATCH -n 1                        # Total number of tasks
#SBATCH -t 01:00:00                # Run time (hh:mm:ss)
#SBATCH --mail-user=andrewigdal17@gmail.com   # Email for notifications
#SBATCH --mail-type=all             # Send email at beginning and end of job

# Load Python module
source ~/miniconda3/etc/profile.d/conda.sh
conda activate project_env

cd $WORK
# Run your Python script
python IGDAL_PROJECT_TASK1_MAKEFERC.py
python IGDAL_PROJECT_TASK2_MERGEWITHHIFLD.py
python IGDAL_PROJECT_TASK3_ROUGHANALYSIS.py
python IGDAL_PROJECT_TASK4_MACHINELEARNING.py


