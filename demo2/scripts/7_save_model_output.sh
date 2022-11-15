#!/bin/bash
# ave use-specified files associated with each model run.
# Preserved files will be stored in directories named "runNNN", where NNN is the iteration_idx.
# This script needs two argument inputs: 
# (1) control_file: "control_active.txt"
# (2) iteration_idx: starting from one.

control_file=$1
iteration_idx=$2

# -----------------------------------------------------------------------------------------
# ------------------------------------ Functions ------------------------------------------
# -----------------------------------------------------------------------------------------
read_from_control () {
    control_file=$1
    setting=$2
    
    line=$(grep -m 1 "^${setting}" $control_file)
    info=$(echo ${line##*|}) # remove the part that ends at "|"
    info=$(echo ${info%%#*}) # remove the part starting at '#'; does nothing if no '#' is present
    echo $info
}

read_from_summa_route_control () {
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
# ------------------------- Settings based on control_file --------------------------------
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

# Extract summa output path and prefix from fileManager.txt.
summa_outputPath="$(read_from_summa_route_control $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_control $summa_filemanager "outFilePrefix")"

# Extract summa parameter file from fileManager.txt.
trialParamFile="$(read_from_summa_route_control $summa_filemanager "trialParamFile")"
trialParamFile_priori=${trialParamFile%\.nc}.priori.nc

trialParamFile=$summa_settings_path/$trialParamFile
trialParamFile_priori=$summa_settings_path/$trialParamFile_priori

# Extract mizuRoute output path and prefix from route_control (use for removing outputs).
route_outputPath="$(read_from_summa_route_control $route_control "<output_dir>")"
route_outFilePrefix="$(read_from_summa_route_control $route_control "<case_name>")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# -----------------------------------------------------------------------------------------
# --------------------------------------- Save --------------------------------------------
# -----------------------------------------------------------------------------------------

outDir="${calib_path}/output_archive"
runDir=$outDir/run$iteration_idx
mkdir -p $runDir

# save multipliers.txt.
cp $calib_path/multipliers.txt $runDir/

# save hydrologic model parameter file and outputs.
cp $trialParamFile $runDir/
cp $summa_outputPath/${summa_outFilePrefix}_day.nc $runDir/
cp $route_outputPath/${route_outFilePrefix}.mizuRoute.nc $runDir/

# save model performance evaluation result.
cp $stat_output $runDir/

exit 0
