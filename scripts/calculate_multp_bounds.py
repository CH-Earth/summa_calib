#!/usr/bin/env python
# coding: utf-8

# #### Calculate multiplier lower/upper bounds ####
# Given the a priori parameter values and the lower/upper bounds in localParam.txt and basinParam.txt, 
# determine globally constant multiplier lower/upper bounds.
# 1. Determine to-be-evaluated multipliers.
# 2. Read the a priori parameter values and lower/upper limits.
# 3. Calculate the multiplier lower/upper bounds.
# 4. Save multiplier bounds into a text.

# import packages
import os, sys, argparse
import numpy as np
import xarray as xr

# define functions
def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to caluclate the multiplier bounds.')
    parser.add_argument('control_file', help='path of the active control file.')
    args = parser.parse_args()
    return(args)

def read_from_control(config_file, setting):
    ''' Function to extract a given setting from the config_file.'''      
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

def read_basinParam_localParam(filename):
    '''Function to extract the param limits from basinParamInfo.txt and localParamInfo.txt'''
    param_names = []
    param_min = []
    param_max =[]
    with open (filename, 'r') as f:
        for line in f:
            line=line.strip()
            if line and not line.startswith('!') and not line.startswith("'"):
                splits=line.split('|')
                if isinstance(splits[0].strip(), str):
                    param_names.append(splits[0].strip())
                    param_min.append(str_to_float(splits[2].strip()))
                    param_max.append(str_to_float(splits[3].strip()))
    return param_names, param_min, param_max

def str_to_float(data_str):
    '''Function to convert data from Fortran format to scientific format.
    Hard coded for Fortran-based summa basinParamInfo.txt and localParamInfo.txt'''
    if 'd' in data_str:
        x = data_str.split('d')[0]+'e'+data_str.split('d')[1]
        return float(x)
    else:
        return float(data_str)


# main
if __name__ == '__main__':
    
    # an example: python prepare_multp_bounds.py ../control_active.txt

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

    # #### 1. Determine evaluated multipliers 
    object_params = read_from_control(control_file, 'object_parameters')    # users provided object params.
    object_multps = [x.strip()+'_multp' for x in object_params.split(',')]  # a list of param multipliers to be estimated. 

    # Add thickness if heightCanopyTop is included in object_parameters.
    # heightCanopyTop is calibrated through thickness and thickness_multp (thickness=heightCanopyTop-heightCanopyBottom).
    if 'heightCanopyTop' in object_params:
        object_multps.append('thickness'+'_multp')  
        object_multps.remove('heightCanopyTop'+'_multp')
    object_multps_num = len(object_multps)

    # #### 2. Read param lower/upper limits
    # Read param range from basinParamInfo.txt and localParamInfo.txt.
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_setting_path     = os.path.join(model_path, summa_settings_relpath)

    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager = os.path.join(summa_setting_path, summa_filemanager)

    # Read file names from summa_filemanager
    basinParam = read_from_summa_route_config(summa_filemanager, 'globalGruParamFile')
    localParam = read_from_summa_route_config(summa_filemanager, 'globalHruParamFile')
    
    # Obtain file paths by adding to summa_setting_path
    basinParam = os.path.join(summa_setting_path, basinParam)
    localParam = os.path.join(summa_setting_path, localParam)
    
    # Read basin and local param names, min and max bounds from basinParam and localParam files.
    basin_param_names, basin_param_min, basin_param_max = read_basinParam_localParam(basinParam)    
    local_param_names, local_param_min, local_param_max = read_basinParam_localParam(localParam)

    # #### 3. Read a priori param values
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_path, summa_settings_relpath)

    trialParamFile = read_from_summa_route_config(summa_filemanager, 'trialParamFile')
    trialParamFile = os.path.join(summa_settings_path, trialParamFile)
    
    # a priori param file generated from 1_generate_priori_trialParam.py.
    trialParamFile_priori = trialParamFile.split('.nc')[0] + '.priori.nc' 
    trialParamFile_priori = os.path.join(summa_settings_path, trialParamFile_priori)
 
    # #### 4. Calculate multiplier lower/upper bounds
    multp_bounds_list = []   # list of [multiplier name, initial, lower, upper]. 

    with xr.open_dataset(trialParamFile_priori) as f:
        for i in range(object_multps_num):
            multp_name = object_multps[i]                # multiplier name (eg, k_soil_multp)
            param_name = multp_name.replace('_multp','') # SUMMA parameter name (eg, k_soil)

            # (1) Read a priori param values.
            if param_name != 'thickness': 
                param_priori = f[param_name].values                                     
            elif param_name == 'thickness': 
                canopyBottom_priori = f['heightCanopyBottom'].values
                canopyTop_priori    = f['heightCanopyTop'].values
                param_priori  = canopyTop_priori - canopyBottom_priori
            
            param_priori_shp = np.shape(param_priori)
            param_priori_ma = np.ma.masked_array(param_priori, mask=(param_priori==0.0))
            if all(param_priori == 0.0):
                print('Error: Parameter %s a-prioir values are all 0.0, \
                so the mutiplier-based calibration is not applicable to it.' %(param_name))
                sys.exit()
        
            # (2) Get param upper and lower limits.                
            if param_name in local_param_names:
                if param_name != 'theta_sat': 
                    index     = local_param_names.index(param_name)
                    param_min = local_param_min[index]*np.ones(param_priori_shp)
                    param_max = local_param_max[index]*np.ones(param_priori_shp)              
                
                elif param_name == 'theta_sat': 
                    index     = local_param_names.index(param_name)
                    param_max = local_param_max[index]*np.ones(param_priori_shp)

                    # Calculate 'theta_sat' param_min which should be larger than \
                    # the max of all other variables of soil_params.
                    soil_params = ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity']

                    # (a) Use a multi-layer array to store the a priori soil_params values \
                    # and the min 'theta_sat' values per hru.
                    nhru  = f.dims['hru']                               # number of hrus. len(f[param_name])
                    nsoil = len(soil_params)+1                          # soil_params variables + 'theta_sat'
                    soil_params_priori_layers = np.ones((nhru,nsoil))                    
                    
                    for isoil in range(nsoil-1):                        # a-priori values for all soil_params variables.
                        soil_param = soil_params[isoil]
                        soil_params_priori_layers[:,isoil] = f[soil_param].values                    
                    
                    # add 'theta_sat' local_param_min to the last layer.
                    soil_params_priori_layers[:,-1] = local_param_min[index]*np.ones(param_priori_shp)  
                    
                    # (b) 'theta_sat' param_min = the max among the a priori values of \
                    # all soil_param variables and the local_param_min per hru.
                    param_min = np.max(soil_params_priori_layers, axis=1)

            elif param_name in basin_param_names:
                if param_name != 'routingGammaScale': 
                    index   = basin_param_names.index(param_name)
                    param_min = basin_param_min[index]*np.ones(param_priori_shp)
                    param_max = basin_param_max[index]*np.ones(param_priori_shp)

                elif param_name == 'routingGammaScale': 
                    # Calculate scale bounds based on GRU river length and runoff velocity.
                    # mean_time_delay = GRU_channel_length / runoff_velocity
                    # routingGammaScale = mean_time_delay / routingGammaShape
                    
                    # (a) Calculate GRU_channel_length (m)
                    # Assume each GRU is a round circle, take its radius as the mean chennel length.                     
                    attributeFile = read_from_summa_route_config(summa_filemanager, 'attributeFile')
                    attributeFile = os.path.join(summa_setting_path, attributeFile)
                    with xr.open_dataset(attributeFile) as fa:
                        nGRU = fa.dims['gru']
                        domain_area = fa['HRUarea'].values.sum()

                    GRU_area = domain_area/nGRU                   # mean GRU area in square meter
                    GRU_channel_length = np.sqrt(GRU_area/np.pi)  # mean GRU chennel length in meter

                    # (b) Calculate routingGammaScale lower and upper bounds.
                    # Assume lower and upper runoff_velocity.
                    v_lower, v_upper = 0.1, 10 # unit: m/s            
                    # Read a priori value of routingGammaShape
                    gammaShape_priori = f['routingGammaShape'].values
                    gammaShape_priori_ma  = np.ma.masked_array(gammaShape_priori, mask=(gammaShape_priori==0.0))

                    param_min = np.divide((GRU_channel_length/v_upper), gammaShape_priori_ma)
                    param_max = np.divide((GRU_channel_length/v_lower), gammaShape_priori_ma)

            elif param_name == 'thickness': 
                # Read a priori canopy bottom and top heights
                index            = local_param_names.index('heightCanopyBottom')
                canopyBottom_min = local_param_min[index]*np.ones(param_priori_shp)
                canopyBottom_max = local_param_max[index]*np.ones(param_priori_shp)   

                index            = local_param_names.index('heightCanopyTop')
                canopyTop_min    = local_param_min[index]*np.ones(param_priori_shp)
                canopyTop_max    = local_param_max[index]*np.ones(param_priori_shp)    

                # Get thickness lower/upper bounds based canopy bottom and top bounds
                param_min        = canopyTop_min - canopyBottom_min
                param_max        = canopyTop_max - canopyBottom_max

            else:
                print('Error: Parameter %s does not exist in localParam.txt and basinParam.txt'%(param_name))
                sys.exit()


            # (3) Determine multiplier feasible range (globally feasible)
            multp_min = np.max(param_min/param_priori_ma)
            multp_max = np.min(param_max/param_priori_ma)
            
            if multp_min>=multp_max:
                print('Error: %s multiplier does not have a feasible range (multiplier min >= multiplier max).'%(param_name))
                sys.exit()
    
            # (4) Update initial multiplier value.
            # When lower_bound < 1 < upper_bound (ie, a priori param value is in the param range), set initial multp = 1.0.
            # If not, set initial multp = 0.5*(lower_bound + upper_bound).
            if (multp_max < 1) or (multp_min > 1):
                multp_initial = np.nanmean([multp_min, multp_max])
            else:
                multp_initial = 1.0
            
            # (5) Append to results to multp_bounds_list.
            multp_bounds_list.append([multp_name, multp_initial, multp_min, multp_max])

    # #### 5. Save multiplier information into text.   
    multp_bounds = os.path.join(calib_path, 'multiplier_bounds.txt')
    if os.path.exists(multp_bounds):
        os.remove(multp_bounds)
    with open(multp_bounds, 'w') as f:
        f.write('# MultiplierName,InitialValue,LowerLimit,UpperLimit.\n')
        for i in range(object_multps_num):
            iList = multp_bounds_list[i]
            f.write('%s,%.6f,%.6f,%.6f\n'%(iList[0],iList[1],iList[2],iList[3]))

    # #### 6. Create multiplier template file and multiplier txt file for the first time.
    # Create a multiplier template file. Write multiplier names.
    multp_tpl = os.path.join(calib_path, 'multipliers.tpl')
    if os.path.exists(multp_tpl):
        os.remove(multp_tpl)
    with open(multp_tpl, 'w') as f:
        for i in range(object_multps_num):
            f.write('%s\n'%(multp_bounds_list[i][0]))
 
    # Create a multiplier txt file. Write multiplier initial values.
    multp_value = os.path.join(calib_path, 'multipliers.txt')
    if os.path.exists(multp_value):
        os.remove(multp_value)
    with open(multp_value, 'w') as f:
        for i in range(object_multps_num):
            f.write('%.6f\n'%(multp_bounds_list[i][1]))
