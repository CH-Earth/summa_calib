#!/bin/bash
#SBATCH --account=<account>
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1 
#SBATCH --mem=2000MB
#SBATCH --job-name=demo4Route
#SBATCH --output=slurm_outputs/%x-%j.out

mkdir -p /home/h294liu/scratch/temp
export TMPDIR=/home/h294liu/scratch/temp
export MPI_SHEPHERD=true

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file=$1   # "control_active.txt"
iteration_idx=$2  # iteration index, starting from one.

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
# Read calibration path from control_file.
calib_path="$(read_from_control $control_file "calib_path")"

# Read hydrologic model path from controlFile.
model_path="$(read_from_control $control_file "model_path")"
if [ "$model_path" = "default" ]; then model_path="${calib_path}/model"; fi

# Read summa and route setting paths.
summa_settings_relpath="$(read_from_control $control_file "summa_settings_relpath")"
summa_settings_path=$model_path/$summa_settings_relpath
route_settings_relpath="$(read_from_control $control_file "route_settings_relpath")"
route_settings_path=$model_path/$route_settings_relpath

# Get summa and mizuRoute configuration files.
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager
route_control="$(read_from_control $control_file "route_control")"
route_control=$route_settings_path/$route_control

# Get mizuRoute executable path.
routeExe="$(read_from_control $control_file "route_exe_path")"

# Extract summa output path and prefix from fileManager.txt (use to remove summa outputs).
summa_outputPath="$(read_from_summa_route_config $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_config $summa_filemanager "outFilePrefix")"

# Extract mizuRoute output path and prefix from route_control (use for removing outputs).
route_outputPath="$(read_from_summa_route_config $route_control "<output_dir>")"
route_outFilePrefix="$(read_from_summa_route_config $route_control "<case_name>")"

# Read DDS max_iterations, warm_start, and initial_option from control_file.
max_iterations="$(read_from_control $control_file "max_iterations")"
warm_start="$(read_from_control $control_file "WarmStart")"
initial_option="$(read_from_control $control_file "initial_option")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# -----------------------------------------------------------------------------------------
# ---------------------------------- Execute trial ----------------------------------------
# -----------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# --- 1.  Post-process summa output for route                                ---
# ------------------------------------------------------------------------------
echo post-process summa output 
date | awk '{printf("%s: post-process summa output\n",$0)}' >> $calib_path/timetrack.log

# Be careful. Hard coded file name "xxx_day.nc". Valid for daily simulation.
# (1) Merge summa daily outputs into one file. 
python scripts/7_concat_summa_ouputs.py $control_file 

# (2) Shift summa output time back 1 day for routing - only if computing daily outputs!
# Summa use end of time step for time values, but mizuRoute use beginning of time step.
ncap2 -h -O -s 'time[time]=time-86400' $summa_outputPath/${summa_outFilePrefix}_day.nc $summa_outputPath/${summa_outFilePrefix}_day.nc

# ------------------------------------------------------------------------------
# --- 2.  Run mizuRoute                                                      ---
# ------------------------------------------------------------------------------

echo run mizuRoute 
date | awk '{printf("%s: run mizuRoute\n",$0)}' >> $calib_path/timetrack.log

# (1) Create mizuRoute output path if it does not exist; and remove existing outputs.
if [ ! -d $route_outputPath ]; then mkdir -p $route_outputPath; fi
rm -f $route_outputPath/${route_outFilePrefix}*

# ##########################################
# NOTE: mip mizuroute needs more tests.
## (2) Prepare files for mipi mizuRoute.
#cp $route_settings_path/param.nml.default $summa_outputPath/param.nml.default
#echo "${summa_outFilePrefix}_day.nc" > $summa_outputPath/summaOutputFileList.txt
#
## (3) Run mizuRoute.
#module load netcdf netcdf-fortran pnetcdf openmpi
#srun ${routeExe} $route_control
#wait
#############################################

# (2) Run mizuRoute.
${routeExe} $route_control

# (3) Merge output runoff into one file for statistics calculation.
ncrcat -O -h $route_outputPath/${route_outFilePrefix}* $route_outputPath/${route_outFilePrefix}.mizuRoute.nc

# ------------------------------------------------------------------------------
# --- 3.  Calculate statistics                                               ---
# ------------------------------------------------------------------------------
echo calculate statistics
date | awk '{printf("%s: calculate statistics\n",$0)}' >> $calib_path/timetrack.log

# # (1) Remove the stats output file to make sure it is created properly with every run.
# rm -f $stat_output

# (2) Calculate statistics.
python scripts/8_calculate_sim_stats.py $control_file
wait

# # ----------------------------------------------------------------------------
# --- 4.  Save param and obj                                                 ---
# ------------------------------------------------------------------------------
echo save param and obj
date | awk '{printf("%s: save param and obj\n",$0)}' >> $calib_path/timetrack.log
python scripts/9_save_param_obj.py $control_file $iteration_idx 

# # ----------------------------------------------------------------------------
# --- 5.  Save model output                                                  ---
# ------------------------------------------------------------------------------
echo save model output
date | awk '{printf("%s: saving model output\n",$0)}' >> $calib_path/timetrack.log
./scripts/10_save_model_output.sh $control_file $iteration_idx

# # ----------------------------------------------------------------------------
# --- 6.  Save the best output                                               ---
# ------------------------------------------------------------------------------
echo save best output
date | awk '{printf("%s: save best output\n",$0)}' >> $calib_path/timetrack.log
python scripts/11_save_best.py $control_file $iteration_idx

# ------------------------------------------------------------------------------
# --- 7.  Generate a new param based on DDS                                  ---
# ------------------------------------------------------------------------------
echo generate a new parameter sample
date | awk '{printf("%s: generate a new parameter sample\n",$0)}' >> $calib_path/timetrack.log

python scripts/4_DDS.py $iteration_idx $max_iterations $initial_option $warm_start \
multiplier_bounds.txt multipliers.tpl multipliers.txt calib_record.txt

# ------------------------------------------------------------------------------
# --- 8.  Update params for summa                                            ---
# ------------------------------------------------------------------------------
echo update params for summa
python scripts/5_update_paramTrial.py $control_file

# ------------------------------------------------------------------------------
# --- 9.  Delete existing summa outputs for the next run                     ---
# ------------------------------------------------------------------------------
echo delete existing summa outputs
date | awk '{printf("%s: delete existing summa outputs\n",$0)}' >> $calib_path/timetrack.log

# Create summa output path if it does not exist; and remove previous outputs.
if [ ! -d $summa_outputPath ]; then mkdir -p $summa_outputPath; fi
rm -f $summa_outputPath/${summa_outFilePrefix}*

date | awk '{printf("%s: done with trial\n",$0)}' >> $calib_path/timetrack.log
date | awk '{printf("%s: ---------------------------\n\n",$0)}' >> $calib_path/timetrack.log
exit 0
