#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import math as m
import os, sys, argparse 

# ======================================================================
# Functions to perturb neighborhoud of decision variables to generate 
# new candidate solutions. Perturbation magnitudes are randomly sampled 
# from the standard normal distribution (mean = zero) 
# code source: https://github.com/t2abdulg/DDS_Py.git
# ======================================================================

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to generate a param set based on DDS.')
    parser.add_argument('iteration_idx', help='input. current iteration id starting from 1.')
    parser.add_argument('warm_start', help='whether use the the best param set of the existing record file. yes or no.')
    parser.add_argument('param_tpl_file', help='param template file where param value is replaced by param name.')
    parser.add_argument('param_file', help='input & output. one set of param sample.')
    parser.add_argument('obj_file', help='input. file storing obj function.')
    parser.add_argument('record_file', help='input & output. calib record file, in the same format as OstModel.txt.')
    args = parser.parse_args()
    return(args)


if __name__ == "__main__":
    
    # Example: python 5_save_best_results.py 1 trial_stats.txt multipliers.txt calib_record.txt

    # process command line 
    # check args
    if len(sys.argv) != 7:
        print("Usage: %s <iteration_idx> <warm_start> <param_tpl_file> <param_file> <obj_file> <record_file>" % sys.argv[0])
        sys.exit(0)
    
    # otherwise continue
    args = process_command_line()    
    iteration_idx = int(args.iteration_idx)# input. current iteration id starting from 1.
    warm_start = args.warm_start           # input. whether use the the best param set of the existing record file. yes or no.
    param_tpl_file = args.param_tpl_file   # input. param template file storing param names.
    param_file = args.param_file           # input. param file storing a set of param sample.
    obj_file = args.obj_file               # input. file storing obj function. 
    record_file = args.record_file         # input & output. param record file.

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
    param_names = list(np.loadtxt(param_tpl_file, dtype='str'))
    param_dim = len(param_names)   # number of parameters
    
    if not os.path.exists(obj_file):
        print('ERROR: = Obj function file %s does not exist.'%(obj_file))            
        quit()
    obj = np.loadtxt(obj_file, usecols=[0]) * (-1) # eg, obj = negative KGE 

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
