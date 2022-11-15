#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import math as m
import os, sys, argparse 
import shutil

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

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to save the best model outputs.')
    parser.add_argument('controlFile', help='path of the overall control file.')
    args = parser.parse_args()
    return(args)

if __name__ == "__main__":
    
    # Example: python save_best.py ../control_active.txt

    # ---------------------------- Preparation -------------------------------
    # Process command line  
    # Check args
    if len(sys.argv) != 2:
        print("Usage: %s <controlFile>" % sys.argv[0])
        sys.exit(0)
    # Otherwise continue
    args = process_command_line()    
    control_file = args.controlFile
        
    # Read calibration path from controlFile
    calib_path = read_from_control(control_file, 'calib_path')

    # Read hydrologic model path from controlFile
    model_path = read_from_control(control_file, 'model_path')
    if model_path == 'default':
        model_path = os.path.join(calib_path, 'model')
        
    # read summa settings and fileManager paths from control_file.
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_path, summa_settings_relpath)
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)

    # read summa output path and prefix.
    summa_outputPath = read_from_summa_route_config(summa_filemanager, 'outputPath')
    summa_outFilePrefix = read_from_summa_route_config(summa_filemanager, 'outFilePrefix')
    summa_output_file = os.path.join(summa_outputPath,summa_outFilePrefix+'_day.nc')
    
    # read mizuRoute setting and control files paths from control_file.
    route_settings_relpath = read_from_control(control_file, 'route_settings_relpath')
    route_settings_path = os.path.join(model_path, route_settings_relpath)
    route_control = read_from_control(control_file, 'route_control')
    route_control = os.path.join(route_settings_path, route_control)

    # read mizuRoute output path and prefix
    route_outputPath = read_from_summa_route_config(route_control, '<output_dir>')
    route_outFilePrefix=read_from_summa_route_config(route_control, "<case_name>")
    route_output_file = os.path.join(route_outputPath, route_outFilePrefix+'.mizuRoute.nc') 

    # summa param file.
    trialParamFile = read_from_summa_route_config(summa_filemanager, 'trialParamFile')
    trialParamFile = os.path.join(summa_settings_path, trialParamFile)
    
    # statistical output file.
    stat_filename = read_from_control(control_file, 'stat_output')
    stat_output = os.path.join(calib_path, stat_filename)

    # =======================================================================
    # check/create output folder
    # =======================================================================
    save_best_dir = os.path.join(calib_path,'output_archive')
    if not os.path.exists(save_best_dir):
        os.makedirs(save_best_dir)    
    stat_best_output = os.path.join(save_best_dir, stat_filename)

    # =======================================================================
    # save results if save_best_dir is empty or a new best solution appears.
    # =======================================================================
    if not os.listdir(save_best_dir):
        shutil.copy2(summa_output_file, save_best_dir)
        shutil.copy2(route_output_file, save_best_dir)
        shutil.copy2(stat_output, save_best_dir)
        shutil.copy2(trialParamFile, save_best_dir)
        shutil.copy2(os.path.join(calib_path,'multiplier*'), save_best_dir)
    else:
        # check if the previous param gets better
        obj_previous = np.loadtxt(stat_output, usecols=[0]) * (-1)  # eg, obj = negative KGE
        obj_best = np.loadtxt(stat_best_output, usecols=[0]) * (-1) 
        
        if obj_previous<obj_best:
            shutil.copy2(summa_output_file, save_best_dir)
            shutil.copy2(route_output_file, save_best_dir)
            shutil.copy2(stat_output, save_best_dir)
            shutil.copy2(trialParamFile, save_best_dir)
            shutil.copy2(os.path.join(calib_path,'multiplier*'), save_best_dir)
