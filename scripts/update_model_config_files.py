#!/usr/bin/env python
# coding: utf-8

# #### Update simulation start and end times in fileManager.txt and mizuroute.control ####
# #### Update intput file name <fname_qsim> in mizuroute.control (eg, "run1_day.nc") ####

# import packages
import os, sys, argparse, shutil
from datetime import datetime
import netCDF4 as nc
import numpy as np

# define functions
def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to update summa and mizuRoute manager/control files.')
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
       
def read_from_summa_route_config(config_file, setting):
    '''Function to extract a given setting from the summa or mizuRoute configuration file.'''
    # Open fileManager.txt or route_control and locate the line with setting
    with open(config_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('!',1)[0].strip().split(None,1)[1].strip("'")
    # Return this value    
    return substring

# main
if __name__ == '__main__':
    
    # an example: python update_model_config_files.py ../control_active.txt

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

    # Read summa and mizuRoute settings paths.
    summa_settings_path = os.path.join(model_path, read_from_control(control_file, 'summa_settings_relpath'))
    route_settings_path = os.path.join(model_path, read_from_control(control_file, 'route_settings_relpath'))

    # Read simulation start and end time from control_file.
    simStartTime = read_from_control(control_file, 'simStartTime')
    simEndTime   = read_from_control(control_file, 'simEndTime') # Note: H:M can be 23:59, but not 24:00. \
                                                                 # 24:00 needs to be replaced by 00:00
    
    # Extract year-month-day, exclude hour-min-sec.
    simStartDate = datetime.strftime(datetime.strptime(simStartTime, '%Y-%m-%d %H:%M'), '%Y-%m-%d')
    simEndDate   = datetime.strftime(datetime.strptime(simEndTime, '%Y-%m-%d %H:%M'), '%Y-%m-%d')

    # -----------------------------------------------------------------------

    # #### 1. Update fileManager.txt by changing simStartTime and simEndTime. 
    # Identify fileManager.txt and a temporary file. 
    summa_filemanager      = os.path.join(summa_settings_path, read_from_control(control_file, 'summa_filemanager'))
    summa_filemanager_temp = summa_filemanager.split('.txt')[0]+'_temp.txt'

    # Change sim times in fileManager.txt            
    with open(summa_filemanager, 'r') as src:
        with open(summa_filemanager_temp, 'w') as dst:
            for line in src:
                if line.startswith('simStartTime'):
                    simStartTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simStartTime_old, "'"+simStartTime+"'")
                elif line.startswith('simEndTime'):
                    simEndTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndTime_old, "'"+simEndTime+"'")
                dst.write(line)
    shutil.copy2(summa_filemanager_temp, summa_filemanager);
    os.remove(summa_filemanager_temp);


    # #### 2. Update mizuRoute route_control by changing simStartTime and simEndTime. 
    # Identify route_control and a temporary file. 
    route_control = os.path.join(route_settings_path, read_from_control(control_file, 'route_control'))
    route_control_temp = route_control.split('.txt')[0]+'_temp.txt'

    # Change sim times in route_control           
    with open(route_control, 'r') as src:
        with open(route_control_temp, 'w') as dst:
            for line in src:
                if line.startswith('<sim_start>'):
                    simStartDate_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simStartDate_old, simStartDate)
                elif line.startswith('<sim_end>'):
                    simEndDate_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndDate_old, simEndDate)
                elif line.startswith('<fname_qsim>'):
                    fname_qsim_old = line.split('!',1)[0].strip().split(None,1)[1] # filename of input runoff from summa
                    outFilePrefix = read_from_summa_route_config(summa_filemanager, 'outFilePrefix') # summa outout FilePrefix
                    fname_qsim_new = outFilePrefix+'_day.nc'
                    line = line.replace(fname_qsim_old, fname_qsim_new)
                dst.write(line)
    shutil.copy2(route_control_temp, route_control);
    os.remove(route_control_temp);
