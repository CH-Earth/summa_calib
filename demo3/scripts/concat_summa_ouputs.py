#!/usr/bin/env python
# coding: utf-8

# #### Concatenate the outputs of a split domain summa run.

import os, sys
from glob import glob
import netCDF4 as nc
import numpy as np
import argparse
from datetime import datetime
import concurrent.futures

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to concatenate summa outputs from multiple GRU subsets.')
    parser.add_argument('controlFile', type=str, help='path of the overall control file.')
    args = parser.parse_args()
    return(args)


def read_from_summa_route_config(control_file, setting):
    '''Function to extract a given setting from the summa or mizuRoute configuration file.'''
    # Open fileManager.txt or route_control and locate the line with setting
    with open(control_file) as ff:
        for line in ff:
            line = line.strip()
            if line.startswith(setting):
                break
    # Extract the setting's value
    substring = line.split('!',1)[0].strip().split(None,1)[1].strip("'")
    # Return this value    
    return substring

def read_from_control(control_file, setting):
    ''' Function to extract a given setting from the controlFile.'''      
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


def concat_summa_outputs(args):
    '''Function to read gru and hru dimensioned variable values and return a dictionary.'''
    # Need inputs: file, gru_vars_num, gru_vars, hru_vars_num, hru_vars.
    file, gru_vars_num, gru_vars, hru_vars_num, hru_vars = args[:]
    
    Dict = {}
    f = nc.Dataset(file) 
    # Read and store variables into Dict
    for j in range(gru_vars_num):
        gru_var_name = gru_vars[j][0]
        data=f.variables[gru_var_name][:].data
        Dict[gru_var_name]=data
                
    for j in range(hru_vars_num):
        hru_var_name = hru_vars[j][0]
        data=f.variables[hru_var_name][:].data
        Dict[hru_var_name]=data            
    return Dict


if __name__ == '__main__':
    
    # an example: python 6b_concat_summa_ouputs.py ../control_active.txt

    # ---------------------------- Preparation -------------------------------
    # Process command line  
    # Check args
    if len(sys.argv) < 2:
        print("Usage: %s <control_file>" % sys.argv[0])
        sys.exit(0)
    # Otherwise continue
    args         = process_command_line()    
    control_file = args.controlFile
    
    # Read calibration path from controlFile
    calib_path = read_from_control(control_file, 'calib_path')

    # Read hydrologic model path from controlFile
    model_path = read_from_control(control_file, 'model_path')
    if model_path == 'default':
        model_path = os.path.join(calib_path, 'model')

    # Identify summa setting path and fileManager.
    summa_settings_path = os.path.join(model_path, read_from_control(control_file, 'summa_settings_relpath'))
    summa_filemanager   = os.path.join(summa_settings_path, read_from_control(control_file, 'summa_filemanager'))

    # Read summa output path and prefix from summa_filemanager
    outputPath = read_from_summa_route_config(summa_filemanager, 'outputPath')
    outFilePrefix = read_from_summa_route_config(summa_filemanager, 'outFilePrefix')
    
    # -----------------------------------------------------------------------

    # # #### 1. Read input and output arguments
    # Get list of split summa output files (hard coded)
    outfilelist = glob((outputPath + outFilePrefix + '*G*_day.nc'))   
    outfilelist.sort()   # not needed, perhaps
    merged_output_file = os.path.join(outputPath,outFilePrefix+'_day.nc') # Be careful. Hard coded.

    # # #### 2. Get the total number of grus and the detailed gruId list (same for hru).
    gru_num,  hru_num   = 0, 0
    gru_list, hru_list = [], []
    for file in outfilelist:
        f = nc.Dataset(file)
        gru_num = gru_num+len(f.dimensions['gru'])
        hru_num = hru_num+len(f.dimensions['hru'])
        
        gru_list.extend(list(f.variables['gruId'][:].data))
        hru_list.extend(list(f.variables['hruId'][:].data))
        
    # # #### 3. Get gru and hru dimensioned variables and build base dictionary for storage
    Dict = {} 
    with nc.Dataset(outfilelist[0]) as src:
        
        time_num = len(src.dimensions['time'])
        
        # 3-1. Identify gru and hru dimensioned variables
        gru_vars = [] # a list of gru dimensioned variable names, gru axis in variable dimension for concatenation. 
        hru_vars = [] # a list of hru dimensioned variable names, hru axis in variable dimension for concatenation. 
        for name, variable in src.variables.items():
            # Assign different values depending on dimension
            dims = variable.dimensions
            if 'gru' in dims:
                gru_vars.append([name,dims.index('gru')])                
            elif 'hru' in dims:
                hru_vars.append([name,dims.index('hru')]) 
        gru_vars_num = len(gru_vars)
        hru_vars_num = len(hru_vars)
        
        # 3-2. Create the base dictionary Dict
        for j in range(gru_vars_num):
            gru_var_name = gru_vars[j][0]
            dim_index = gru_vars[j][1]
            if dim_index == 0:
                Dict[gru_var_name]=np.zeros((gru_num,))
            elif dim_index == 1:
                Dict[gru_var_name]=np.zeros((time_num,gru_num))
            else:
                print('Variable %s has more than two dimensions: time and gru. '%(gru_var_name))
                sys.exit()
        for j in range(hru_vars_num):
            hru_var_name = hru_vars[j][0]
            dim_index = hru_vars[j][1]
            if dim_index == 0:
                Dict[hru_var_name]=np.zeros((hru_num,))
            elif dim_index == 1:
                Dict[hru_var_name]=np.zeros((time_num,hru_num))
            else:
                print('Variable %s has more than two dimensions: time and hru. '%(gru_var_name))
                sys.exit()
    
    # # #### 4. Loop summa output files, parallel reading and serial saving.  
    # reference: https://docs.python.org/3/library/concurrent.futures.html
    # print('concatenate outputs')
    # start_time = datetime.now() 
    args = ([file, gru_vars_num, gru_vars, hru_vars_num, hru_vars] for file in outfilelist)
    with concurrent.futures.ProcessPoolExecutor() as executor:    
        for file_i, Dict_i in zip(outfilelist, executor.map(concat_summa_outputs, args)):
            f = nc.Dataset(file_i) 

            # Get the gru and hru indices for file_i
            gruId = list(f.variables['gruId'][:].data)
            gru_start_idx = gru_list.index(gruId[0])
            gru_end_idx = gru_list.index(gruId[-1])

            hruId = list(f.variables['hruId'][:].data)
            hru_start_idx = hru_list.index(hruId[0])
            hru_end_idx = hru_list.index(hruId[-1])

            # Store Dict_i variables into Dict
            for j in range(gru_vars_num):
                gru_var_name = gru_vars[j][0]
                dim_index = gru_vars[j][1]
                if dim_index == 0:
                    Dict[gru_var_name][gru_start_idx:gru_end_idx+1]=Dict_i[gru_var_name]
                elif dim_index == 1:
                    Dict[gru_var_name][:,gru_start_idx:gru_end_idx+1]=Dict_i[gru_var_name]

            for j in range(hru_vars_num):
                hru_var_name = hru_vars[j][0]
                dim_index = hru_vars[j][1]
                if dim_index == 0:
                    Dict[hru_var_name][hru_start_idx:hru_end_idx+1]=Dict_i[hru_var_name]
                elif dim_index == 1:
                    Dict[hru_var_name][:,hru_start_idx:hru_end_idx+1]=Dict_i[hru_var_name]
    # print(datetime.now() - start_time)

    # # #### 5. Write output    
    # print('write outputs')
    # start_time = datetime.now()    
    with nc.Dataset(outfilelist[0]) as src:
        with nc.Dataset(merged_output_file, "w") as dst:

            # Copy dimensions
            for name, dimension in src.dimensions.items():
                if name == 'gru':
                    dst.createDimension(name, gru_num)
                elif name == 'hru':
                    dst.createDimension(name, hru_num)
                else:
                    dst.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

            # Copy variable attributes all at once via dictionary
            for name, variable in src.variables.items():
                x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                dst[name].setncatts(src[name].__dict__)
                # Note here the variable dimension name is the same, but size has been updated for gru and hru.

                # Assign different values depending on dimension
                dims = variable.dimensions
                if not ('gru' in dims) and not ('hru' in dims):
                    dst[name][:]=src[name][:]                

            # Assign values for gru and hru dimensioned variables
            for j in range(gru_vars_num):
                dst.variables[gru_vars[j][0]][:] = Dict[gru_vars[j][0]]
            for j in range(hru_vars_num):
                dst.variables[hru_vars[j][0]][:] = Dict[hru_vars[j][0]]

    # print(datetime.now() - start_time)
