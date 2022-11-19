#!/bin/bash
# Save use-specifed files every time a best paraemter set is discovered.

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file="control_active.txt"  # path of the active control file

# -----------------------------------------------------------------------------------------
# ------------------------------------ Functions ------------------------------------------
# -----------------------------------------------------------------------------------------
# Function to extract a given setting from the control_file.
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
# ------------------------- Settings based on control_file --------------------------------
# -----------------------------------------------------------------------------------------
# Read calibration path from control_file.
calib_path="$(read_from_control $control_file "calib_path")"

# Read hydrologic model path from control_file.
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
summa_outputPath="$(read_from_summa_route_config $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_config $summa_filemanager "outFilePrefix")"

# Extract summa parameter file from fileManager.txt.
trialParamFile="$(read_from_summa_route_config $summa_filemanager "trialParamFile")"
trialParamFile_priori=${trialParamFile%\.nc}.priori.nc

trialParamFile=$summa_settings_path/$trialParamFile
trialParamFile_priori=$summa_settings_path/$trialParamFile_priori

# Extract mizuRoute output path and prefix from route_control (use for removing outputs).
route_outputPath="$(read_from_summa_route_config $route_control "<output_dir>")"
route_outFilePrefix="$(read_from_summa_route_config $route_control "<case_name>")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# -----------------------------------------------------------------------------------------
# -------------------------------------- Execute ------------------------------------------
# -----------------------------------------------------------------------------------------

outDir="${calib_path}/output_archive"
mkdir -p $outDir

echo "saving input and output files for the best solution."

# save control_file
cp $calib_path/$control_file $outDir/

# save multiplier related files.
cp $calib_path/multiplier* $outDir/

# save hydrologic model control files, parameter file and outputs.
cp $summa_filemanager $outDir/
cp $route_control $outDir/ 

cp $trialParamFile $outDir/
cp $trialParamFile_priori $outDir/

cp $summa_outputPath/${summa_outFilePrefix}_day.nc $outDir/
cp $route_outputPath/${summa_outFilePrefix}.mizuRoute.nc $outDir/

# save model performance evaluation result and Ostrich output files.
cp $stat_output $outDir/
cp $calib_path/Ost*.txt $outDir/
cp $calib_path/timetrack.log $outDir/

exit 0

