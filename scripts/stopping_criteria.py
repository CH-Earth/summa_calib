#!/usr/bin/env python
# coding: utf-8

# #### Calculate stopping criteria for model calibration.

# import packages
import os, sys, datetime, argparse
import pandas as pd
import xarray as xr

# define functions
def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to calculate model evaluation statistics KGE.')
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
       
def read_from_ostoutput(ostoutput_file, kstop):
    '''Function to extract a given setting from the summa or mizuRoute configuration file.'''
    # Open fileManager.txt or route_control and locate the line with setting
    count = 0
    with open(ostoutput_file) as ff:
        lines = ff.readlines()
        for line in lines:
            count += 1
            if line.startswith('Optimal Parameter Set'):
                break
    # Extract the objective function value
    
    mylines = lines[(count-2-kstop):(count-2)]
    of_values = []
    last_trial = 0
    for myline in mylines:
        
        if len(myline.split()) != 0 and myline.split()[0].isnumeric():
            of_values.append(float(myline.split()[1]))
            last_trial = int(myline.split()[0])
    
    # Return this value    
    return of_values, last_trial

# main
if __name__ == '__main__':
    
    # an example: python stopping_criteria.py ../control_active.txt

    # ------------------------------ Prepare ---------------------------------
    # Process command line  
    # Check args
    if len(sys.argv) < 2:
        print("Usage: %s <control_file>" % sys.argv[0])
        sys.exit(0)
    # Otherwise continue
    args         = process_command_line()    
    control_file = args.control_file
    
    # Read calibration path from control_file
    calib_path   = read_from_control(control_file, 'calib_path')

    # OstModel0.txt
    ostoutput_file = os.path.join(calib_path, 'OstOutput0.txt')
    
    
    # Read arguments for stopping criteria
    maxn = int(read_from_control(control_file, 'max_iterations'))
    kstop = int(read_from_control(control_file, 'loop_stagnation'))
    pcento = float(read_from_control(control_file, 'per_change'))
    
    # -----------------------------------------------------------------------

    # #### 1. Read objective function values from OstModel0.txt
    of_values, last_trial = read_from_ostoutput(ostoutput_file, kstop)
    
    # #### 2. Stopping criteria
    if (len(of_values) == kstop) and (last_trial == maxn or abs(of_values[0]-of_values[-1]) <= of_values[0] * pcento/100):
        ### stop Ostrich exe
        ostquit_file = os.path.join(calib_path, 'OstQuit.txt')
        open(ostquit_file, "a").close()
    
