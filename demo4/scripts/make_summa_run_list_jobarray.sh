#!/bin/bash
# Make a job list to run summa in parallel across requested cores.
# Note: This code is specifically used for array jobs (via offset).
# This script needs six argument inputs as explained as follows.

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file=$1   # "control_active.txt"
startGRU=$2       # startGRU index 
endGRU=$3         # endGRU index 
nSubset=$4        # number of GRU subsets
countGRU=$5       # size of a GRU subset  
offset=$6         # array job index (Should start from zero for calculations below)

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

# -----------------------------------------------------------------------------------------
# -------------------------------------- Execute ------------------------------------------
# -----------------------------------------------------------------------------------------
# Copy summaExe to local to save summa_run_list.txt size
cp $summaExe summa.exe
chmod 744 summa.exe

# remove existing summa_run_list.txt.
[ ! -d summa_run_lists ] && mkdir summa_run_lists
jobList=summa_run_lists/summa_run_list_${offset}.txt
rm -f $jobList

# Loop to write each GRU subset per line
iSubset=0
while [ $iSubset -lt $nSubset ]; do

    # Set gru bounds per subset; 
    iStartGRU=$(( startGRU + iSubset*countGRU ))
    iEndGRU=$(( iStartGRU + countGRU - 1 ))
    
    # Adjust countGRU to cap at max of endGRU
   if [ $iEndGRU -gt $endGRU ]; then 
        iCountGRU=$(( endGRU - iStartGRU + 1 ))
    else 
        iCountGRU=$countGRU
    fi    

    # Write a subset per line to jobList
    echo $iSubset ./summa.exe -g $iStartGRU $iCountGRU -r never -m $summa_filemanager >> $jobList
      
    iSubset=$(( iSubset + 1 ))
done
