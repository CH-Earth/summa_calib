#!/usr/bin/env python
# coding: utf-8

# #### Calculate model performance evaluation/statistical metrics.

# import module
import os, sys, datetime, argparse, glob
import numpy as np
import pandas as pd
import xarray as xr

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to calculate model evaluation statistics KGE.')
    parser.add_argument('control_file', help='path of the active control file.')
    args = parser.parse_args()
    return(args)

def get_modified_KGE(obs,sim): 
    '''Modified KGE reference: Kling, Harald, Martin Fuchs, and Maria Paulin. \
    "Runoff conditions in the upper Danube basin under an ensemble of climate change scenarios." \
    Journal of hydrology 424 (2012): 264-277.'''
    sd_sim = np.std(sim, ddof=1)
    sd_obs = np.std(obs, ddof=1)
    
    m_sim  = np.mean(sim)
    m_obs  = np.mean(obs)
    
    r      = (np.corrcoef(sim,obs))[0,1]
    relvar = (float(sd_sim)/float(m_sim))/(float(sd_obs)/float(m_obs))
    bias   = float(m_sim)/float(m_obs)
    
    kge    = 1.0-np.sqrt((r-1)**2 +(relvar-1)**2 + (bias-1)**2)
    return kge

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
    
    # an example: python 5b_calculate_sim_stats.py ../control_active.txt

    # ---------------------------- Preparation -------------------------------
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

    # Read hydrologic model path from control_file
    model_path = read_from_control(control_file, 'model_path')
    if model_path == 'default':
        model_path = os.path.join(calib_path, 'model')

    # read mizuRoute setting and control file paths from control_file.
    route_settings_path = os.path.join(model_path, read_from_control(control_file, 'route_settings_relpath'))
    route_control       = os.path.join(route_settings_path, read_from_control(control_file, 'route_control'))

    # -----------------------------------------------------------------------

    # #### 1. Read input and output arguments 
    # Specify mizuRoute output file
    output_dir          = read_from_summa_route_config(route_control, '<output_dir>')
    route_outFilePrefix = read_from_summa_route_config(route_control, "<case_name>")
    
    # Specify segment id, observations, statistics relevant configs.
    q_seg_index = int(read_from_control(control_file, 'q_seg_index')) # start from one.
    
    obs_file = read_from_control(control_file, 'obs_file')
    obs_unit = read_from_control(control_file, 'obs_unit')

    statStartDate = read_from_control(control_file, 'statStartDate') 
    statEndDate   = read_from_control(control_file, 'statEndDate')

    # Convert str date to datetime 
    time_format   = '%Y-%m-%d'
    statStartDate = datetime.datetime.strptime(statStartDate,time_format)
    statEndDate   = datetime.datetime.strptime(statEndDate,time_format)    

    # Specify the statistical output file.
    stat_output = os.path.join(calib_path, read_from_control(control_file, 'stat_output'))

    # #### 2. Calculate 
    # --- Read simulated flow (cms) --- 
    # Note: simVarName is hard coded for the demo output. Users can modify based on their output.
    simVarName   = 'IRFroutedRunoff'
    simFile      = os.path.join(output_dir, route_outFilePrefix+'.mizuRoute.nc') # Hard coded file name. Be careful.
    f            = xr.open_dataset(simFile)
    time         = f['time'].values
    sim          = f[simVarName][:,(q_seg_index-1)].values  # IRFroutedRunoff is in dim (time, segments)
    df_sim       = pd.DataFrame({'sim':sim},index = time)
    df_sim.index = pd.to_datetime(df_sim.index)

    # --- Read observed flow (cfs or cms) --- 
    # Note: this is hard coded for the demo observation file. Users can modify based on their observation file.
    df_obs = pd.read_csv(obs_file, index_col=0, na_values=["-99.0","-999.0","-9999.0","NA"],
                         usecols=[0,1],parse_dates=True, infer_datetime_format=True)  
    df_obs.columns = ['obs'] 
    
    # Convert obs from cfs to cms
    if obs_unit == 'cfs':
        df_obs = df_obs/35.3147    
        
    # --- Merge the two df based on time index--- 
    df_sim_eval = df_sim.truncate(before=statStartDate, after=statEndDate)
    df_obs_eval = df_obs.truncate(before=statStartDate, after=statEndDate)
    df_merge    = pd.concat([df_obs_eval, df_sim_eval], axis=1)
    df_merge    = df_merge.dropna()

    # --- Calculate diagnostics --- 
    kge = get_modified_KGE(obs=df_merge['obs'].values, sim=df_merge['sim'].values)
    
    # #### 3. Save 
    f = open(stat_output, 'w+')
    f.write('%.6f' %kge + '\t#KGE\n')
    f.close()
