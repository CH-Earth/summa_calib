#!/usr/bin/env python
# coding: utf-8

# #### Create ostIn.txt
# This code creates ostIn.txt based on the user specified parameter list.
# 1. prepare Ostrich parameter pair files based on multiplier bounds file.
# 2. write ostIn.txt based on ostIn.tpl.

# import packages
import os, sys, argparse, shutil, time
import netCDF4 as nc
import numpy as np

# define functions
def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to create Ostrich ostIn.txt.')
    parser.add_argument('control_file', help='path of the active control file.')
    args = parser.parse_args()
    return(args)

def read_from_control(control_file, setting):
    ''' Function to extract a given setting from the control_file.'''      
    # Open 'control_active.txt' and locate the line with setting
    with open(control_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('|',1)[1].split('#',1)[0].strip() 
    # Return this value    
    return substring


# main
if __name__ == '__main__':
    
    # an example: python create_ostIn.py ../control_active.txt

    # ------------------------------ Prepare ---------------------------------
    # Process command line  
    # Check args
    if len(sys.argv) != 2:
        print("Usage: %s <control_file>" % sys.argv[0])
        sys.exit(0)
    # Otherwise continue
    args = process_command_line()    
    control_file = args.control_file

    # Read calibration path from control_file
    calib_path = read_from_control(control_file, 'calib_path')

    # Read hydrologic model path from control_file
    model_path = read_from_control(control_file, 'model_path')
    if model_path == 'default':
        model_path = os.path.join(calib_path, 'model')
    
    # -----------------------------------------------------------------------

    # #### 1. Prepare Ostrich parameter pair files
    # Specify the multiplier template file and multiplier txt file.
    multp_tpl = os.path.join(calib_path, 'multipliers.tpl')
    multp_value = os.path.join(calib_path, 'multipliers.txt')

    # Read multiplier bounds file generated from 2_calculate_multp_bounds.py.
    multp_bounds     = os.path.join(calib_path, 'multiplier_bounds.txt')
    multp_bounds_arr = np.loadtxt(multp_bounds, dtype='str', delimiter=',') # MultiplierName,InitialValue,LowerLimit,UpperLimit.
    multp_num        = len(multp_bounds_arr)
    
    # #### 2. Write ostIn.txt based on ostIn.tpl   
    # Identify ostIn template and txt file.
    ostIn_src = os.path.join(calib_path, read_from_control(control_file, 'ostIn_tpl'))
    ostIn_dst = os.path.join(calib_path, 'ostIn.txt')

    # Check if template ostIn file exists.
    if not os.path.exists(ostIn_src):
        print('Template ostIn file does not exist: %s'%(ostIn_src))
        sys.exit(0)

    # Find out the line numbers with BeginFilePairs...EndFilePairs and BeginParams...EndParams configurations
    with open(ostIn_src,"r") as src:
        for number, line in enumerate(src):
            line_strip = line.strip()

            if line.startswith('EndFilePairs'):
                filePairs_line_number = number # to add filePairs config before this line

            elif line.startswith('EndParams'):
                param_line_number = number     # to add param config before this line

    # Write ostIn.txt based on ostIn.tpl
    with open(ostIn_src,"r") as src:
        with open(ostIn_dst,"w") as dst:
            for number, line in enumerate(src):
                line_strip = line.strip()

                if line_strip and (not (line_strip.startswith('#'))):  

                    # (1) Add BeginFilePairs...EndFilePairs configurations. 
                    if number==filePairs_line_number:

                        # Identify the multp_tpl and multp_value paths relative to calib_path 
                        tpl_relpath = os.path.relpath(multp_tpl, start = calib_path)
                        value_relpath = os.path.relpath(multp_value, start = calib_path)
                        
                        # Add the relative multp_tpl and multp_value paths.
                        add_line = ('%s; %s\n')%(tpl_relpath, value_relpath)                                
                        dst.write(add_line)

                    # (2) Add BeginParams...EndParams configurations. 
                    if number==param_line_number:
                        for i in range(multp_num):
                            # Identify the multiplier information
                            multp_name = multp_bounds_arr[i,0]
                            multp_ini  = multp_bounds_arr[i,1]
                            multp_min  = multp_bounds_arr[i,2]
                            multp_max  = multp_bounds_arr[i,3]
                            # Add these information to ostIn_dst.
                            add_line = ('%s\t%s\t%.7f\t%.7f\tnone\tnone\tnone\tfree\n')% \
                            (multp_name, multp_ini, float(multp_min), float(multp_max))                                 
                            dst.write(add_line)

                    # (3) Add random seed to ostIn_dst.
                    if ('xxxxxxxxx' in line_strip):
                        rand_num_digit  = 9  # digit number of random seed
                        t               = int(time.time()*(10**rand_num_digit))
                        t_cut           = t-(int(t/(10**rand_num_digit)))*(10**rand_num_digit)
                        line_strip      = line_strip.replace('xxxxxxxxx',str(t_cut))

                    # (4) Update Ostrich restart based on the existence of 'OstModel0.txt'.
                    if (line_strip.startswith('OstrichWarmStart')):
                        warm_status = read_from_control(control_file, 'WarmStart')
                        if warm_status.lower() == 'yes':
                            line_strip = 'OstrichWarmStart yes'
                        elif warm_status.lower() == 'no':
                            line_strip = 'OstrichWarmStart no' 

                    # (5) Update MaxIterations based on control_active.txt 
                    # Note: this is applied only if the DDS algorithm is used.
                    max_iterations = read_from_control(control_file, 'max_iterations')
                    if line_strip.startswith('MaxIterations'):
                        max_iterations_old = line.split('#',1)[0].strip().split(None,1)[1]
                        line_strip = line_strip.replace(max_iterations_old, max_iterations)                    

                new_line = line_strip+'\n'    
                dst.write(new_line)
