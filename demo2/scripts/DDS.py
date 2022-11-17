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
    parser.add_argument('iteration_idx', help='current iteration id starting from 1.')
    parser.add_argument('max_iterations', help='max iteration limit.')
    parser.add_argument('initial_option', help="initial value option: 'UseInitialParamValues' or 'UseRandomParamValues'.")
    parser.add_argument('warm_start', help='whether use the the best param set of the existing record file. yes or no.')
    parser.add_argument('param_bounds_file', help='param feasible range file.')
    parser.add_argument('param_tpl_file', help='param template file where param value is replaced by param name.')
    parser.add_argument('param_file', help='param file that stores one set of param sample.')
    parser.add_argument('param_record_file', help='param record file that saves all the param searching history.')
    args = parser.parse_args()
    return(args)

def perturb_type(s,s_min,s_max,discrete_flag):
    
    if discrete_flag == 0:
        # perturb continuous variable
        s_new = perturb_cont(s,s_min,s_max)
    else:
        # perturb discrete variable
        s_new = perturb_disc(s,s_min,s_max)
    return s_new

def perturb_cont(s,s_min,s_max):
        
        # Define parameter range
        s_range = s_max - s_min
        # Scalar neighbourhood size perturbation parameter (r) 
        # NOTE: this value is proven to be robust. **DO NOT CHANGE**
        r = 0.2
        # Perturb variable
        z_value = stand_norm() 
        delta = s_range*r*z_value 
        #delta = s_range*r*np.random.randn(1)
        s_new = s + delta
        
        # Handle perturbations outside of decision variable range:
        # Reflect and absorb decision variable at bounds
        
        # probability of absorbing or reflecting at boundary
        P_Abs_or_Ref = np.random.random()
        
        # Case 1) New variable is below lower bound
        if s_new < s_min: # works for any pos or neg s_min
            if P_Abs_or_Ref <= 0.5: # with 50% chance reflect
                s_new = s_min + (s_min - s_new) 
            else: # with 50% chance absorb
                s_new = s_min.copy()
            # if reflection goes past s_max then value should be s_min since without reflection
            # the approach goes way past lower bound.  This keeps X close to lower bound when X current
            # is close to lower bound:
            if s_new > s_max:
                s_new = s_min.copy()

        # Case 2) New variable is above upper bound
        elif s_new > s_max:  #works for any pos or neg s_max
            if P_Abs_or_Ref <= 0.5:  #with 50% chance reflect
                s_new = s_max - (s_new - s_max) 
            else:  # with 50% chance absorb
                s_new = s_max.copy()
            # if reflection goes past s_min then value should be s_max for same reasons as above
            if s_new < s_min:
                s_new = s_max.copy()

        return s_new

def perturb_disc(s,s_min,s_max):
    # ==================================================== 
    # Function for discrete decision variable perturbation
    # ====================================================        
    # Define parameter range
    s_range = s_max - s_min
    # Scalar neighbourhood size perturbation parameter (r) 
    # NOTE: this value is proven to be robust. **DO NOT CHANGE**
    r = 0.2;
    # Perturb variable
    z_value = stand_norm 
    delta = s_range*r*z_value
    s_new = s + delta
    
    # Handle perturbations outside of decision variable range:
    # Reflect and absorb decision variable at bounds
    
    # probability of absorbing or reflecting at boundary
    P_Abs_or_Ref = np.random.rand(1)
    
    # Case 1) New variable is below lower bound
    if s_new < s_min - 0.5: # works for any pos or neg s_min
        if P_Abs_or_Ref <= 0.5: # with 50% chance reflect
            s_new = (s_min-0.5) + ((s_min-0.5) - s_new) 
        else: # with 50% chance absorb
            s_new = s_min          
        # if reflection goes past s_max+0.5 then value should be s_min since without reflection
        # the approach goes way past lower bound.  This keeps X close to lower bound when X current
        # is close to lower bound:
        if s_new > s_max + 0.5:
            s_new = s_min

    # Case 2) New variable is above upper bound
    elif s_new > s_max + 0.5:  #works for any pos or neg s_max
        if P_Abs_or_Ref <= 0.5:  #with 50% chance reflect
            s_new = (s_max+0.5) - (s_new - (s_max+0.5))
        else:  # with 50% chance absorb
            s_new = s_max
        # if reflection goes past s_min -0.5 then value should be s_max for same reasons as above
        if s_new < s_min - 0.5:
            s_new = s_max
            
    # Round new value to nearest integer
    s_new = np.around(s_new)
    
    # Handle case where new value is the same as current: sample from 
    # uniform distribution
    if s_new == s:
        samp = s_min - 1 + np.ceil(s_range)*np.random.rand()
        if samp < s:
            s_new = samp
        else:
            s_new = samp+1

    return s_new  

def stand_norm():
    # Function returns a standard Gaussian random number (zvalue)  
    # based upon Numerical recipes gasdev and Marsagalia-Bray Algorithm
    Work3=2.0 
    while( (Work3>=1.0) or (Work3==0.0) ):
    # call random_number(ranval) # get one uniform random number
        ranval = np.random.random() #harvest(ign)
        Work1 = 2.0 * ranval - 1.0  #2.0 * DBLE(ranval) - 1.0
    # call random_number(ranval) # get one uniform random number
        ranval = np.random.random() #harvest(ign+1)
        Work2 = 2.0 * ranval - 1.0 # 2.0 * DBLE(ranval) - 1.0
        Work3 = Work1 * Work1 + Work2 * Work2
        # ign = ign + 2

    Work3 = ((-2.0 * m.log(Work3)) / Work3)**0.5  # natural log
        
    # pick one of two deviates at random (don't worry about trying to use both):
    # call random_number(ranval) # get one uniform random number
    ranval = np.random.random() #harvest(ign)
    # ign = ign + 1

    if (ranval < 0.5) : 
        zvalue = Work1 * Work3
    else :
        zvalue = Work2 * Work3

    return zvalue


if __name__ == "__main__":
    
    # Example: python DDS.py 1 10 UseInitialParamValues no \
    # multiplier_bounds.txt multipliers.tpl multipliers.txt ParamValuesRecord.txt

    # process command line 
    # check args
    if len(sys.argv) != 9:
        print("Usage: %s <iteration_idx> <max_iterations> <initial_option> <warm_start> <param_bounds_file> <param_tpl_file> <param_file> <param_record_file> " % sys.argv[0])
        sys.exit(0)
    
    # otherwise continue
    args = process_command_line()    
    iteration_idx = int(args.iteration_idx)              # input. current iteration id starting from 1
    max_iterations = int(args.max_iterations)            # input. max iteration.
    initial_option = args.initial_option                 # input. initial value option: 'UseInitialParamValues' or 'UseRandomParamValues'
    warm_start = args.warm_start                         # input. whether use the the best param set of the existing record file. yes or no.
    param_bounds_file = args.param_bounds_file           # input. file storing param range
    param_tpl_file = args.param_tpl_file                 # input. param template file where param value is replaced by param name.
    param_file = args.param_file                         # input & output. one set of param sample.
    param_record_file = args.param_record_file           # input & output. param record file.


    # read param initials and ranges
    param_bounds_df = pd.read_csv(param_bounds_file, delimiter=',', comment='#', 
                                  names=['MultiplierName','InitialValue','LowerLimit','UpperLimit'])                  
    
    param_dim = len(param_bounds_df)                     # total number of parameters
    param_names = param_bounds_df.iloc[:,0]              # param name array
    param_lower_limit, param_upper_limit = param_bounds_df['LowerLimit'].values, param_bounds_df['UpperLimit'].values 
    param_range = param_upper_limit - param_lower_limit  # param range array
    discrete_flags = np.zeros((param_dim))               # 1: discrete param. 0: continuous param
    
    # =======================================================================
    # Define the initial param set 
    # =======================================================================
    if iteration_idx==1:
        
        # Use the best param set of the existing param record file as the initial
        if warm_start=='yes' and os.path.exists(param_record_file):
            param_record_df = pd.read_csv(param_record_file, header='infer', skip_blank_lines=True,
                                          delim_whitespace=True, engine='python')
            best_idx = np.nanargmin(param_record_df['obj.function'])
            param_names = param_record_df.columns.values[2:] # skip the first two columns (Run, obj)
            param_sample = param_record_df.iloc[best_idx,2:].values
         
        # Use a brand new param set as the initial
        else:
            if initial_option == 'UseInitialParamValues':
                param_sample = param_bounds_df['InitialValue'].values
            elif initial_option == 'UseRandomParamValues':
                if discrete_flags.all() == 0: # handling continuous variables  
                    # return continuous uniform random samples 
                    param_sample = param_lower_limit + param_range*np.random.random(param_dim)  
                else: # handling discrete case
                    param_sample = np.zeros((param_dim,))
                    for i_param in range(param_dim):
                        # return random integers from the discrete uniform dist'n
                        param_sample[i_param] = np.random.randit([param_lower_limit[i_param], param_upper_limit[i_param]],size=1) 

    # =======================================================================
    # Generate a new sample param set based on DDS
    # reference: https://github.com/t2abdulg/DDS_Py.git
    # =======================================================================
    elif iteration_idx>1: 
        
        # read the previous param values from param_file
        if not os.path.exists(param_file):
            print('ERROR: Param file %s does not exist.'%(param_file))            
            quit()
        param_sample_previous = np.loadtxt(param_file) 

        # basic definitions
        select_param_count = 0                   # number of decision variables that vary in neighbour
        rand_numbers=np.random.random(param_dim) # random number array for pertubation        
        Pn=1.0-m.log1p(iteration_idx)/m.log(max_iterations)  # probability of being selected as neighbour
        param_sample = param_sample_previous.copy()
        
        # define a sample of param set
        for i_param in range(param_dim):
            # then the i^th param selected to vary in neighbour
            if rand_numbers[i_param]< Pn: 
                select_param_count=select_param_count+1
                param_sample[i_param] = perturb_type(param_sample_previous[i_param], param_lower_limit[i_param], 
                                        param_upper_limit[i_param], discrete_flags[i_param])

        # no params selected at random, so select ONE.   
        if select_param_count==0: 
            # which param to modify for neighbour 
            i_param=int(m.floor((param_dim)*np.random.random(1)))
            param_sample[i_param] = perturb_type(param_sample_previous[i_param], param_lower_limit[i_param], 
                                        param_upper_limit[i_param], discrete_flags[i_param])

    # =======================================================================
    # Output the new sample param set
    # =======================================================================
    # read param name list from the template file
    param_names_tpl = list(np.loadtxt(param_tpl_file, dtype='str'))

    # write param value based on the param name
    with open(param_file,'w') as f:
        for i_param in range(len(param_names_tpl)):
            param_idx = param_names_tpl.index(param_names[i_param])
            f.write('%.6E\n'%(param_sample[param_idx]))
                
    # print(param_sample)
