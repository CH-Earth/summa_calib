#!/bin/bash

# -----------------------------------------------------------------------------------------
# ----------------------------- User specified input --------------------------------------
# -----------------------------------------------------------------------------------------
control_file=control_active.txt
summa_job_file=run_summa.sh
route_job_file=run_route.sh

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

# Extract summa output path and prefix from fileManager.txt (use to remove summa outputs).
summa_outputPath="$(read_from_summa_route_config $summa_filemanager "outputPath")"
summa_outFilePrefix="$(read_from_summa_route_config $summa_filemanager "outFilePrefix")"

# Read DDS max_iterations, warm_start, and initial_option from control_file.
max_iterations="$(read_from_control $control_file "max_iterations")"
warm_start="$(read_from_control $control_file "WarmStart")"
initial_option="$(read_from_control $control_file "initial_option")"

# -----------------------------------------------------------------------------------------
# ------------------------------------ Execute  -------------------------------------------
# -----------------------------------------------------------------------------------------

# ### Prepare ###
echo "===== Prepare ====="
# (1) Generate the a priori parameter file for calibration.
echo "----- Generate a priori parameter file -----"
python scripts/1_generate_priori_trialParam.py $control_file

# (2) Calculate the parameter multiplier lower and upper bounds.
echo "----- Calculate multiplier bounds -----"
python scripts/2_calculate_multp_bounds.py $control_file

# (3) Update summa and mizuRoute start/end time based on control_file.
echo "----- Update summa and mizuRoute configuration files -----"
python scripts/3_update_model_config_files.py $control_file

# (4) Create slurm output folder if not exist
if [ ! -d slurm_outputs ]; then mkdir slurm_outputs; fi

# -----------------------------------------------------------------------------------------
# ---------------------------------- Submit jobs ------------------------------------------
# -----------------------------------------------------------------------------------------

# submit depedent jobs by updating next and current
#for iteration_idx in $(seq 1 $max_iterations); do
for iteration_idx in $(seq 1 2); do
    echo iteration $iteration_idx

    # ------------------------------------------------------------------------------
    # The first iteration jobs.
    # ------------------------------------------------------------------------------
    if [ "$iteration_idx" -eq 1 ]; then
        # ------------------------------------------------------------------------------
        # --- 1.  Generate params via DDS                                            ---
        # ------------------------------------------------------------------------------
	python scripts/4_DDS.py $iteration_idx $max_iterations $initial_option $warm_start \
    	multiplier_bounds.txt multipliers.tpl multipliers.txt calib_record.txt
	
	# ------------------------------------------------------------------------------
	# --- 2.  Update params for summa                                             ---
	# ------------------------------------------------------------------------------
	python scripts/5_update_paramTrial.py $control_file

        # ------------------------------------------------------------------------------
        # --- 3.  Submit run summa & route                                           ---
        # ------------------------------------------------------------------------------
        # (1) Create summa output path if it does not exist; and remove previous outputs.
        if [ ! -d $summa_outputPath ]; then mkdir -p $summa_outputPath; fi
        rm -f $summa_outputPath/${summa_outFilePrefix}*

        # (2) Submit the 1st job: run summa (array job)       
        current=$( sbatch ${summa_job_file} ${control_file} | awk '{ print $4 }' )  # $4 is used to return jobid
        echo summa $current
        
	# (3) Submit depedent job: run route and all others except run summa
        next=$( sbatch --dependency=afterok:${current} ${route_job_file} ${control_file} ${iteration_idx} \
	| awk '{ print $4 }' )
	current=$next
	echo route $current

    # ------------------------------------------------------------------------------
    # The following iteration jobs.
    # ------------------------------------------------------------------------------
    else   

        # ------------------------------------------------------------------------------
        # --- 1.  Submit run summa & route                                           ---
        # ------------------------------------------------------------------------------
	# (1) Submit depedent job: run summa (array job)
	next=$( sbatch --dependency=afterok:${current} ${summa_job_file} ${control_file} | awk '{ print $4 }' )
        current=$next
        echo summa $current
        
	# (2) Submit depedent job: run route and all others except run summa
        next=$( sbatch --dependency=afterok:${current} ${route_job_file} ${control_file} ${iteration_idx} \
	| awk '{ print $4 }' )
        current=$next
        echo route $current
    fi
done

exit 0
