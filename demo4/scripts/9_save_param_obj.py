#!/usr/bin/env python
# coding: utf-8

# Save the seaching history of parameters and their corresponding objective function values \
# to calib_record.txt ####
# This script needs two argument inputs:
# (1) control_file: "control_active.txt"
# (2) iteration_idx: starting from one.

# import module
import numpy as np
import pandas as pd
import math as m
import os, sys, argparse 

def read_from_control(control_file, setting):
    ''' Function to extract a given setting from the controlFile'''
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

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to generate a param set based on DDS.')
    parser.add_argument('controlFile', help='path of the overall control file.')
    parser.add_argument('iteration_idx', help='input. current iteration id starting from 1.')
    args = parser.parse_args()
    return(args)


if __name__ == "__main__":
    
    # Example: python 9_save_param_obj.py ../control_active.txt 1 

    # process command line 
    # check args
    if len(sys.argv) != 3:
        print("Usage: %s <controlFile> <iteration_idx>" % sys.argv[0])
        sys.exit(0)
    
    # otherwise continue
    args = process_command_line()    
    control_file  = args.controlFile       # input. path of the active control file.    
    iteration_idx = int(args.iteration_idx)# input. current iteration id starting from 1.
    
    # Read calibration path from controlFile
    calib_path = read_from_control(control_file, 'calib_path')

    # Read DDS max_iterations, warm_start, and initial_option from control_file.
    max_iterations = read_from_control(control_file, 'max_iterations')
    warm_start     = read_from_control(control_file, 'WarmStart')
    initial_option = read_from_control(control_file, 'initial_option')

    # Get statistical output file from control_file.
    stat_output = read_from_control(control_file, 'stat_output')
    stat_output = os.path.join(calib_path, stat_output)

    # Specify other files
    param_tpl_file = 'multipliers.tpl'      # param template file storing param names.
    param_file     = 'multipliers.txt'      # param file storing a set of param sample.
    record_file    = 'calib_record.txt'     # param and obj record file.

    # =======================================================================
    # Read param sample, name, and obj function. 
    # =======================================================================
    if not os.path.exists(param_file):
        print('ERROR: Param file %s does not exist.'%(param_file))            
        quit()
    param_sample = np.loadtxt(param_file) 

    if not os.path.exists(param_tpl_file):
        print('ERROR: = Param template file %s does not exist.'%(param_tpl_file))            
        quit()
    param_names = list(np.loadtxt(param_tpl_file, dtype='str')) # a list of parameter names
    param_dim   = len(param_names)                              # number of parameters
    
    if not os.path.exists(stat_output):
        print('ERROR: = Obj function file %s does not exist.'%(stat_output))            
        quit()
    obj = np.loadtxt(stat_output, usecols=[0]) * (-1)  # objective function, eg, obj = negative KGE 

    # =======================================================================
    # Save to record_file
    # =======================================================================
    if warm_start=='no' and iteration_idx==1:
        if os.path.exists(record_file):    
            os.remove(record_file)
    
    # create a new record_file
    if not os.path.exists(record_file):               
        with open(record_file, 'w') as f:
            
            # write param name list
            f.write('Run obj.function ')
            for i_param in range(param_dim):
                f.write(param_names[i_param]+'\t')
            f.write('\n')
            
            # write initial obj and param values
            f.write('1 %.6E '%(obj))
            for i_param in range(param_dim):
                f.write('%.6E '%(param_sample[i_param]))
            f.write('\n')            

    # append to an existing record file
    else: 
        record_df = pd.read_csv(record_file, header='infer', skip_blank_lines=True,
                                      engine='python') #delim_whitespace=True, 
        previous_run_count = len(record_df)
        
        with open(record_file, 'a') as f:            
            # write the i^th obj and param values
            f.write('%d %.6E '%(previous_run_count+1, obj))
            for i_param in range(param_dim):
                f.write('%.6E '%(param_sample[i_param]))
            f.write('\n')                    

    # =======================================================================
    # Print 
    # =======================================================================
    # print title line
    param_names_str = ''
    for i_param in range(param_dim):
        param_names_str = param_names_str + '%s '%(param_names[i_param])
    print('Run Obj %s'%(param_names_str))
     
    # print param + obj
    param_sample_str = ''
    for i_param in range(param_dim):
        param_sample_str = param_sample_str + '%.6E '%(param_sample[i_param])
    print('%d %.6E %s'%(iteration_idx,obj,param_sample_str))
