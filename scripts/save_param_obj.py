#!/usr/bin/env python
# coding: utf-8

# Save the searching history of parameters and their corresponding objective function values to two files:\
# (1) calib_search_history.txt: record each model run param and obj.
# (2) calib_converge_history.txt: save param and obj every time a bew best param is discovered.

# This script needs two argument inputs:
# (1) control_file: "control_active.txt"
# (2) iteration_idx: starting from one.

# import packages
import os, sys, argparse 
import numpy as np
import pandas as pd

# define functions
def read_from_control(control_file, setting):
    ''' Function to extract a given setting from the control_file'''
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
    parser.add_argument('control_file', help='path of the overall control file.')
    parser.add_argument('iteration_idx', help='input. current iteration id starting from 1.')
    args = parser.parse_args()
    return(args)

# main
if __name__ == "__main__":
    
    # Example: python save_param_obj.py ../control_active.txt 1 

    # ------------------------------ Prepare ---------------------------------
    # process command line 
    # check args
    if len(sys.argv) != 3:
        print("Usage: %s <control_file> <iteration_idx>" % sys.argv[0])
        sys.exit(0)
    
    # otherwise continue
    args = process_command_line()    
    control_file  = args.control_file       # input. path of the active control file.    
    iteration_idx = int(args.iteration_idx)# input. current iteration id starting from 1.
    
    # Read calibration path from control_file
    calib_path = read_from_control(control_file, 'calib_path')

    # Read DDS max_iterations, warm_start, and initial_option from control_file.
    max_iterations = read_from_control(control_file, 'max_iterations')
    warm_start     = read_from_control(control_file, 'WarmStart')
    initial_option = read_from_control(control_file, 'initial_option')

    # Get statistical output file from control_file.
    stat_output = read_from_control(control_file, 'stat_output')
    stat_output = os.path.join(calib_path, stat_output)

    # Specify other files
    param_tpl_file     = os.path.join(calib_path, 'multipliers.tpl')            # param template file storing param names.
    param_file         = os.path.join(calib_path, 'multipliers.txt')            # param file storing a set of param sample.
    search_file   = os.path.join(calib_path, 'calib_search_history.txt')   # param and obj search history file.
    converge_file = os.path.join(calib_path, 'calib_converge_history.txt') # param and obj converge historyfile.

    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 1. Read param sample, name, and obj function. 
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # 2. Create converge_file and search_file
    # -----------------------------------------------------------------------
    if warm_start=='no' and iteration_idx==1:
        if os.path.exists(converge_file):    
            os.remove(converge_file)
        if os.path.exists(search_file):    
            os.remove(search_file)

    # Use flag to avoid duplicate adding a record.
    # 0: this file exists, do not create. Just add the record later. 
    # 1: this file does not exist, create. No need to add the record again later. 
    converge_file_flag = 0  
    search_file_flag   = 0  

    # Create a new converge_file 
    if not os.path.exists(converge_file): 
        converge_file_flag = 1
        with open(converge_file, 'w') as f:
            
            # write param name list
            f.write('Run  obj.function  ')
            for i_param in range(param_dim):
                f.write(param_names[i_param]+'  ')
            f.write('\n')
            
            # write initial obj and param values
            f.write('1 %.6E  '%(obj))
            for i_param in range(param_dim):
                f.write('%.6E  '%(param_sample[i_param]))
            f.write('\n')            

    # Create a new search_file 
    if not os.path.exists(search_file): 
        search_file_flag = 1
        with open(search_file, 'w') as f:
            
            # write param name list
            f.write('Run  obj.function  ')
            for i_param in range(param_dim):
                f.write(param_names[i_param]+'  ')
            f.write('\n')
            
            # write initial obj and param values
            f.write('1 %.6E  '%(obj))
            for i_param in range(param_dim):
                f.write('%.6E  '%(param_sample[i_param]))
            f.write('\n')    
            
    # -----------------------------------------------------------------------
    # 3. Add to converge_file and search_file
    # -----------------------------------------------------------------------
    # NOTE: update converge_file before updating search_file because, at this time, 
    # the current run param and obj are not included in search_file yet.
    
    # (1) Read existing search history.
    record_df = pd.read_csv(search_file, header='infer', skip_blank_lines=True,
                            delim_whitespace=True, engine='python')  
    previous_run_count = len(record_df)
    obj_best  = record_df['obj.function'].min()

    # (2) Add to converge_file if this record has not been added and obj<=obj_best.
    if converge_file_flag == 0: # use flag to avoid duplicate adding a record.
        if obj<=obj_best:
            with open(converge_file, 'a') as f:            
                # write the i^th obj and param values
                f.write('%d %.6E  '%(previous_run_count+1, obj))
                for i_param in range(param_dim):
                    f.write('%.6E  '%(param_sample[i_param]))
                f.write('\n')   

    # (3) Add to search_file if this record has not been added .
    if search_file_flag == 0: # use flag to avoid duplicate adding a record.
        with open(search_file, 'a') as f:            
            # write the i^th obj and param values
            f.write('%d %.6E  '%(previous_run_count+1, obj))
            for i_param in range(param_dim):
                f.write('%.6E  '%(param_sample[i_param]))
            f.write('\n')                    
                           
    # -----------------------------------------------------------------------
    # 4. Print to screen for update
    # -----------------------------------------------------------------------
    # Print title line
    param_names_str = ''
    for i_param in range(param_dim):
        param_names_str = param_names_str + '%s  '%(param_names[i_param])
    print('Run  obj.function  %s'%(param_names_str))
     
    # Print param and obj
    param_sample_str = ''
    for i_param in range(param_dim):
        param_sample_str = param_sample_str + '%.6E  '%(param_sample[i_param])
    print('%d  %.6E  %s'%(iteration_idx,obj,param_sample_str))
