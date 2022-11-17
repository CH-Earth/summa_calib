#!/bin/bash
# Run interaction of Ostrich: update params, run and route model, calculate diagnostics.
# Create a time tracking log to monitor pace of calibration.
# When use on cluster: module load python; module load nco.

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file="control_active.txt"  # path of the active control file

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
# ---------------------- Read configurations from control_file ----------------------------
# -----------------------------------------------------------------------------------------

# Read calibration path from controlFile.
calib_path="$(read_from_control $control_file "calib_path")"

# Read hydrologic model path from controlFile.
model_path="$(read_from_control $control_file "model_path")"
if [ "$model_path" = "default" ]; then model_path="${calib_path}/model"; fi

# Read summa and mizuRoute setting paths.
summa_settings_relpath="$(read_from_control $control_file "summa_settings_relpath")"
summa_settings_path=$model_path/$summa_settings_relpath
route_settings_relpath="$(read_from_control $control_file "route_settings_relpath")"
route_settings_path=$model_path/$route_settings_relpath

# Get summa and mizuRoute controls/fileManager files.
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager
route_control="$(read_from_control $control_file "route_control")"
route_control=$route_settings_path/$route_control

# Get summa and mizuRoute executable paths.
summaExe="$(read_from_control $control_file "summa_exe_path")"
routeExe="$(read_from_control $control_file "route_exe_path")"

# Get the numebr of GRUs for the domain (used for splitting summa run).
summa_attributeFile="$(read_from_summa_route_config $summa_filemanager "attributeFile")"
summa_attributeFile=$summa_settings_path/$summa_attributeFile
nGRU=$( ncks -Cm -v gruId -m $summa_attributeFile | grep 'gru = '| cut -d' ' -f 7 )

# Extract summa output path and prefix from fileManager.txt (use to remove summa outputs).
summa_outputPath="$(read_from_summa_route_config $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_config $summa_filemanager "outFilePrefix")"

# Extract mizuRoute output path and prefix from route_control (use for removing outputs).
route_outputPath="$(read_from_summa_route_config $route_control "<output_dir>")"
route_outFilePrefix="$(read_from_summa_route_config $route_control "<case_name>")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# -----------------------------------------------------------------------------------------
# ---------------------------------- Execute trial ----------------------------------------
# -----------------------------------------------------------------------------------------

echo "===== executing trial ====="
date | awk '{printf("%s: ---- executing new trial ----\n",$0)}' >> $calib_path/timetrack.log

# ------------------------------------------------------------------------------
# --- 1.  Update params                                                      ---
# ------------------------------------------------------------------------------
echo "--- updating params ---"
date | awk '{printf("%s: update params\n",$0)}' >> $calib_path/timetrack.log
python scripts/update_paramTrial.py $control_file
echo " "

# ------------------------------------------------------------------------------
# --- 2.  Run summa                                                          ---
# ------------------------------------------------------------------------------
echo "--- run summa ---"
date | awk '{printf("%s: run summa\n",$0)}' >> $calib_path/timetrack.log

# (1) Create summa output path if it does not exist; and remove previous outputs.
if [ ! -d $summa_outputPath ]; then mkdir -p $summa_outputPath; fi
rm -f $summa_outputPath/${summa_outFilePrefix}*

# (2) Run Summa.
${summaExe} -r never -m $summa_filemanager

# ------------------------------------------------------------------------------
# --- 3.  Post-process summa output for route                                ---
# ------------------------------------------------------------------------------
echo "--- post-process summa output ---"
date | awk '{printf("%s: post-process summa output\n",$0)}' >> $calib_path/timetrack.log
# Hard coded file name "xxx_day.nc". Valid for daily simulation.
# Shift summa output time back 1 day for routing - only if computing daily outputs!
# Summa use end of time step for time values, but mizuRoute use beginning of time step.
ncap2 -h -O -s 'time[time]=time-86400' $summa_outputPath/$summa_outFilePrefix\_day.nc $summa_outputPath/$summa_outFilePrefix\_day.nc

# ------------------------------------------------------------------------------
# --- 4.  Run mizuRoute                                                      ---
# ------------------------------------------------------------------------------
echo "--- run mizuRoute ---"
date | awk '{printf("%s: run mizuRoute\n",$0)}' >> $calib_path/timetrack.log

# (1) Create mizuRoute output path if it does not exist; and remove existing outputs.
if [ ! -d $route_outputPath ]; then mkdir -p $route_outputPath; fi
rm -f $route_outputPath/${route_outFilePrefix}*

# (2) Run mizuRoute.
${routeExe} $route_control
wait

# (3) Merge output runoff into one file for statistics calculation. Hard coded output file name.
ncrcat -O -h $route_outputPath/${route_outFilePrefix}* $route_outputPath/${route_outFilePrefix}.mizuRoute.nc

# ------------------------------------------------------------------------------
# --- 5.  Calculate statistics                                               ---
# ------------------------------------------------------------------------------
echo "--- calculating statistics ---"
date | awk '{printf("%s: calculate statistics\n",$0)}' >> $calib_path/timetrack.log
python scripts/calculate_sim_stats.py $control_file 

date | awk '{printf("%s: done with trial\n",$0)}' >> $calib_path/timetrack.log

exit 0
