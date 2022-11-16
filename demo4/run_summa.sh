#!/bin/bash
#SBATCH --account=rpp-kshook
#SBATCH --time=00:30:00
#SBATCH --array=0-2
#SBATCH --ntasks=2
#SBATCH --mem-per-cpu=100MB
#SBATCH --job-name=demo4Summa
#SBATCH --output=slurm_outputs/%x-%A_%a.out

mkdir -p /home/h294liu/scratch/temp
export TMPDIR=/home/h294liu/scratch/temp
export MPI_SHEPHERD=true

#-----------------------------------------------------------------------------------------
# RUN WITH:
# sbatch --array1-[number of jobs] [script name]
# sbatch --array=0-842 1_summa_array_to_copernicus.sh
# reference: https://docs.computecanada.ca/wiki/Job_arrays
# ----------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file=$1   # "control_active.txt"
nJob=3            # number of jobs in job array. Should be the same as in --array.
nSubset=2         # number of GRU subsets in summa GRUs split. Should be the same as in --ntasks.

# -----------------------------------------------------------------------------------------
# ------------------------------------ Functions ------------------------------------------
# -----------------------------------------------------------------------------------------
# Function to extract a given setting from the controlFile.
read_from_control () {
    control_file=$1
    setting=$2
    
    line=$(grep -m 1 "^${setting}" $control_file)
    info=$(echo ${line##*|}) # remove the part that ends at "|"
    info=$(echo ${info%%#*}) # remove the part starting at '#'; does nothing if no '#' is present
    echo $info
}

# Function to extract a given setting from the summa or mizuRoute configuration file.
read_from_summa_route_config () {
    input_file=$1
    setting=$2

    line=$(grep -m 1 "^${setting}" $input_file)
    info=$(echo ${line%%!*}) # remove the part starting at '!'
    info="$( cut -d ' ' -f 2- <<< "$info" )" # get string after the first space
    info="${info%\'}" # remove the suffix '. Do nothing if no '.
    info="${info#\'}" # remove the prefix '. Do nothing if no '.
    echo $info
}

# -----------------------------------------------------------------------------------------
# -------------------------- Read settings from control_file ------------------------------
# -----------------------------------------------------------------------------------------
# Read calibration path from controlFile.
calib_path="$(read_from_control $control_file "calib_path")"

# Read hydrologic model path from controlFile.
model_path="$(read_from_control $control_file "model_path")"
if [ "$model_path" = "default" ]; then model_path="${calib_path}/model"; fi

# Read summa setting and summa_filemanager paths.
summa_settings_relpath="$(read_from_control $control_file "summa_settings_relpath")"
summa_settings_path=$model_path/$summa_settings_relpath
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager

# Get summa executable path.
summaExe="$(read_from_control $control_file "summa_exe_path")"

# Read the total numebr of GRUs (used to calculate countGRU).
summa_attributeFile="$(read_from_summa_route_config $summa_filemanager "attributeFile")"
summa_attributeFile=$summa_settings_path/$summa_attributeFile
nGRU=$( ncks -Cm -v gruId -m $summa_attributeFile | grep 'gru = '| cut -d' ' -f 7 )

# -----------------------------------------------------------------------------------------
# ------------------------------------ Run summa ------------------------------------------
# -----------------------------------------------------------------------------------------
# (1) Calculate countGRU. 
countGRU=$(( ( $nGRU / ($nJob * $nSubset) ) + ( $nGRU % ($nJob * $nSubset)  > 0 ) )) 

# (2) Get the array ID for further use
offset=$SLURM_ARRAY_TASK_ID 

# (3) Calcualte gruStart and gruEnd for job array
gruStart=$(( 1 + countGRU*nSubset*offset ))
gruEnd=$(( countGRU*nSubset*(offset+1) ))

# Check that we don't specify too many basins
if [ $gruEnd -gt $nGRU ]; then
    gruEnd=$nGRU
fi

# (4) Make summa_run_list for job array
./scripts/6_make_summa_run_list_jobarray.sh $control_file $gruStart $gruEnd $nSubset $countGRU $offset

# (5) Run job array 
srun --kill-on-bad-exit=0 --multi-prog summa_run_lists/summa_run_list_${offset}.txt 

