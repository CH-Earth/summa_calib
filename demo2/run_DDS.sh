#!/bin/bash

# Run DDS Python code-based calibration.

#### Note: When use on cluster: module load python; module load nco.

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file=control_active.txt

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
# -------------------------- Read settings from control_file ------------------------------
# -----------------------------------------------------------------------------------------
# Read calibration path from control_file.
calib_path="$(read_from_control $control_file "calib_path")"

# Read hydrologic model path from control_file.
model_path="$(read_from_control $control_file "model_path")"
if [ "$model_path" = "default" ]; then model_path="${calib_path}/model"; fi

# Read summa setting and summa_filemanager paths.
summa_settings_relpath="$(read_from_control $control_file "summa_settings_relpath")"
summa_settings_path=$model_path/$summa_settings_relpath
summa_filemanager="$(read_from_control $control_file "summa_filemanager")"
summa_filemanager=$summa_settings_path/$summa_filemanager

# Extract summa output path and prefix from fileManager.txt (use to remove summa outputs).
summa_outputPath="$(read_from_summa_route_config $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_config $summa_filemanager "outFilePrefix")"

# Read DDS max_iterations, warm_start, and initial_option from control_file.
max_iterations="$(read_from_control $control_file "max_iterations")"
warm_start="$(read_from_control $control_file "WarmStart")"
initial_option="$(read_from_control $control_file "initial_option")"

# Get statistical output file from control_file.
stat_output="$(read_from_control $control_file "stat_output")"
stat_output=${calib_path}/${stat_output}

# -----------------------------------------------------------------------------------------
# ------------------------------------ Execute  -------------------------------------------
# -----------------------------------------------------------------------------------------

# ### Prepare ###
echo "===== Prepare ====="
# (1) Generate the a priori parameter file for calibration.
echo "----- Generate a priori parameter file -----"
python ../scripts/generate_priori_trialParam.py $control_file

# (2) Calculate the parameter multiplier lower and upper bounds.
echo "----- Calculate multiplier bounds -----"
python ../scripts/calculate_multp_bounds.py $control_file

# (3) Update summa and mizuRoute start/end time based on control_file.
echo "----- Update summa and mizuRoute configuration files -----"
python ../scripts/update_model_config_files.py $control_file


# ### Run DDS ###
echo "===== Run DDS  ====="
for iteration_idx in $(seq 1 $max_iterations); do
    
    echo "----- iteration $iteration_idx -----"
    
    # # ----------------------------------------------------------------------------
    # --- 1.  generate a new sample param set                                    ---
    # ------------------------------------------------------------------------------
    echo generate param sett
    date | awk '{printf("%s: generate parameter set\n",$0)}' >> $calib_path/timetrack.log
    
    python ../scripts/DDS.py $iteration_idx $max_iterations $initial_option $warm_start \
    $calib_path/multiplier_bounds.txt $calib_path/multipliers.tpl \
    $calib_path/multipliers.txt $calib_path/calib_converge_history.txt
    
    # # ----------------------------------------------------------------------------
    # --- 2.  conduct run_trial.sh                                               ---
    # ------------------------------------------------------------------------------
    echo run trial
    date | awk '{printf("%s: run trial\n",$0)}' >> $calib_path/timetrack.log    
    ./run_trial.sh > ExeOut.txt
    
    # # ----------------------------------------------------------------------------
    # --- 3.  save param and obj                                                  ---
    # ------------------------------------------------------------------------------
    echo save param and obj
    date | awk '{printf("%s: save param and obj\n",$0)}' >> $calib_path/timetrack.log
    python ../scripts/save_param_obj.py $control_file $iteration_idx

    # # ----------------------------------------------------------------------------
    # --- 4.  save model output                                              ---
    # ------------------------------------------------------------------------------
    echo save model output
    date | awk '{printf("%s: saving model output\n",$0)}' >> $calib_path/timetrack.log
    ../scripts/save_model_output.sh $control_file $iteration_idx

    # # ----------------------------------------------------------------------------
    # --- 5.  save the best output                                              ---
    # ------------------------------------------------------------------------------
    echo save best output
    date | awk '{printf("%s: save best output\n\n",$0)}' >> $calib_path/timetrack.log
    python ../scripts/save_best.py $control_file $iteration_idx

done

exit
