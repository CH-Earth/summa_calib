#!/bin/bash
#SBATCH --account=<account>
#SBATCH --time=01:00:00
#SBATCH --nodes=2
#SBATCH --ntasks=51
#SBATCH --mem=10000MB
#SBATCH --job-name=demo3
#SBATCH --output=%x-%j.out

#### Note: This bash file must be put in the same directory as Ostrich.exe.
#### Note: When use on cluster: module load python; module load nco.

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified inputs -------------------------------------
# -----------------------------------------------------------------------------------------
control_active=control_active.txt  # path of the active control file
nSubset=51                         # number of GRU subsets to split summa run. Suggest being consistent with the above ntasks.

# -----------------------------------------------------------------------------------------
# ------------------------------------ Execute  -------------------------------------------
# -----------------------------------------------------------------------------------------

# ### Prepare ###
echo "===== Prepare ====="
# (1) Generate the a priori parameter file for calibration.
echo "----- Generate a priori parameter file -----"
python ../scripts/generate_priori_trialParam.py $control_active

# (2) Calculate the parameter multiplier lower and upper bounds.
echo "----- Calculate multiplier bounds -----"
python ../scripts/calculate_multp_bounds.py $control_active

# (3) Update summa and mizuRoute start/end time based on control_active.txt.
echo "----- Update summa and mizuRoute configuration files -----"
python ../scripts/update_model_config_files.py $control_active

# (4) Create ostIn.txt by adding multiplier and other configurations.
echo "----- Create ostIn.txt -----"
python ../scripts/create_ostIn.py $control_active

# (5) Make a summa_run_list to split and parallalize summa runs based on nSubset.
echo "----- Make summa_run_list -----"
../scripts/make_summa_run_list.sh $control_active $nSubset


# ### Run Ostrich ###
echo "===== Run Ostrich ====="
./Ostrich.exe
