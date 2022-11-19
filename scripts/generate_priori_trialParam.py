#!/usr/bin/env python
# coding: utf-8

# #### Create a priori trial parameter file (trialParam.priori.nc) ####
# Given a list of SUMMA parameter names, create their corresponding a priori parameter values. 
# 1. Update outputControl.txt by adding parameter names.
# 2. Update fileManager.txt by changing simStartTime and simEndTime. 
#    Here use a 1-day simulation to get the a priori parameter values.
# 3. Run SUMMA to get a priori parameter values in timestep summa output. 
# 4. Extract a priori parameter values from summa output and generate trialParam.priori.nc.

# import module
import os, sys, argparse, shutil, datetime
import netCDF4 as nc
import numpy as np

def process_command_line():
    '''Parse the commandline'''
    parser = argparse.ArgumentParser(description='Script to prepare the a-priori summa trialParam.nc.')
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
    
    # An example: python 1_generate_priori_trialParam.py ../control_active.txt

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
    summa_settings_relpath = read_from_control(control_file, 'summa_settings_relpath')
    summa_settings_path = os.path.join(model_path, summa_settings_relpath)

    # Identify fileManager.txt and define a temporary file. 
    summa_filemanager = read_from_control(control_file, 'summa_filemanager')
    summa_filemanager_temp = summa_filemanager.split('.txt')[0]+'_temp.txt'

    summa_filemanager = os.path.join(summa_settings_path, summa_filemanager)
    summa_filemanager_temp = os.path.join(summa_settings_path, summa_filemanager_temp)

    # Identify outputControl.txt and define a temporary file.
    outputControlFile = read_from_summa_route_config(summa_filemanager, 'outputControlFile')
    outputControlFile_temp = outputControlFile.split('.txt')[0]+'_temp.txt'
    
    outputControlFile = os.path.join(summa_settings_path, outputControlFile)
    outputControlFile_temp = os.path.join(summa_settings_path, outputControlFile_temp)

    # Identify summa output, attribtue, and trialParam files
    outputPath = read_from_summa_route_config(summa_filemanager, 'outputPath')
    outFilePrefix = read_from_summa_route_config(summa_filemanager, 'outFilePrefix')
    outputFile = os.path.join(outputPath, outFilePrefix+'_timestep.nc')

    trialParamFile = read_from_summa_route_config(summa_filemanager, 'trialParamFile')
    trialParamFile_priori = trialParamFile.split('.nc')[0] + '.priori.nc' # a priori param file

    trialParamFile = os.path.join(summa_settings_path, trialParamFile)
    trialParamFile_priori = os.path.join(summa_settings_path, trialParamFile_priori)

    attributeFile = read_from_summa_route_config(summa_filemanager,'attributeFile')
    attributeFile = os.path.join(summa_settings_path, attributeFile)
    
    # -----------------------------------------------------------------------

    # #### 1. Update summa outputControl.txt by adding parameter names.
    # Determine summa output parameters. 
    # Note object_params and output_params are not necessarily the same.
    object_params = read_from_control(control_file, 'object_parameters')  # users provided param names
    output_params = [x.strip() for x in object_params.split(',')]         # a more complete list of params \
    # that should be included in the a priori parameter file due to the constrains \
    # between parameters (eg, soil and canopy height related parameters as shown below)

    # Add more parameters if any soil water content parameters are included in object_params.
    soil_params = ['theta_res', 'critSoilWilting', 'critSoilTranspire', 'fieldCapacity', 'theta_sat']
    if any(soil_param in object_params for soil_param in soil_params):
        for soil_param in soil_params:
            if not soil_param in object_params:
                output_params.append(soil_param)            

    # Add more parameters if canopy height parameters are included in object_params.
    height_params = ['heightCanopyBottom', 'heightCanopyTop']
    if any(height_param in object_params for height_param in height_params):
        for height_param in height_params:
            if not height_param in object_params:
                output_params.append(height_param)   
                
    # Add output_params to outputControl.txt            
    with open(outputControlFile, 'r') as src:
        content = src.read()
        with open(outputControlFile_temp, 'w') as dst:
            for param in output_params:
                if not param in content:
                    dst.write(param)
                    dst.write('\n')
            dst.write(content)
    shutil.copy2(outputControlFile_temp, outputControlFile);
    os.remove(outputControlFile_temp);

    
    # #### 2. Update fileManager.txt by changing simStartTime and simEndTime. 
    simStartTime = read_from_control(control_file, 'simStartTime')
    simStartTime_priori = simStartTime  # in format 'yyyy-mm-dd hh:mm'
    simEndTime_priori = datetime.datetime.strftime(datetime.datetime.strptime(simStartTime, '%Y-%m-%d %H:%M') \
                                                   + datetime.timedelta(days=1), '%Y-%m-%d %H:%M') 

    # Change sim times in fileManager.txt            
    with open(summa_filemanager, 'r') as src:
        with open(summa_filemanager_temp, 'w') as dst:
            for line in src:
                if line.startswith('simStartTime'):
                    simStartTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simStartTime_old, simStartTime_priori)
                elif line.startswith('simEndTime'):
                    simEndTime_old = line.split('!',1)[0].strip().split(None,1)[1]
                    line = line.replace(simEndTime_old, simEndTime_priori)
                dst.write(line)
    shutil.copy2(summa_filemanager_temp, summa_filemanager);
    os.remove(summa_filemanager_temp);


    # #### 3. Run SUMMA model to get a priori parameter values in summa output
    # Summa executable
    summa_exe_path = read_from_control(control_file, 'summa_exe_path')

    # Remove existing summa parameter files
    if os.path.exists(trialParamFile):
        os.remove(trialParamFile)
    if os.path.exists(trialParamFile_priori):
        os.remove(trialParamFile_priori)

    # Remove summa output path if it exists and create from scratch.
    if os.path.isdir(outputPath):
            shutil.rmtree(outputPath)
    os.makedirs(outputPath)        

    # Run SUMMA
    cmd = summa_exe_path + ' -m '+ summa_filemanager
    os.system(cmd)


    # #### 4. Extract a priori parameter values from summa timestep output and generate trialParam.priori.nc.
    # Open summa output and attribute files for reading
    with nc.Dataset(outputFile, 'r') as ff:
        with nc.Dataset(attributeFile) as src:

            # Create trialParamFile_priori based on attributeFile.
            with nc.Dataset(trialParamFile_priori, "w") as dst:

                # Copy dimensions from attributeFile
                for name, dimension in src.dimensions.items():
                     dst.createDimension(
                        name, (len(dimension) if not dimension.isunlimited() else None))

                # Copy gurId and hruId variables from attributeFile
                include = ['gruId', 'hruId']
                for name, variable in src.variables.items():
                    if name in include:
                        x = dst.createVariable(name, variable.datatype, variable.dimensions)               
                        dst[name].setncatts(src[name].__dict__)
                        dst[name][:]=src[name][:] 

                # Create parameter variables one-by-one
                for param_name in output_params:

                    # Get param dimension from summa output
                    param_dims = ff[param_name].dimensions

                    # Get param value from summa output
                    if param_name != 'routingGammaScale':

                        # k_macropore, k_soil, theta_sat with dim (depth, hru).
                        if param_dims == ('depth','hru'):
                            param_value = ff[param_name][0,:] # use the first depth value.

                        # other params with dim (hru) or (gru).
                        elif param_dims == ('hru',) or param_dims == ('gru',):
                            param_value = ff[param_name][:] 

                        else:
                            print('Parameter %s has dimensions more than gru, hru, depth:\n \
                            Check before moving forward.'%(param_name), param_dims)
                            sys.exit()
                    
                    # Calculate a-priori value for GammaScale (gru) based on GRU river length and runoff velocity
                    elif param_name == 'routingGammaScale': 
                        # (1) Read a-priori value of GammaShape
                        shape_priori = ff['routingGammaShape'][:]

                        # (2) Calculate gru streamline length (m)
                        # Assume GRU is a round circle, take its radius as the mean chennel length. 
                        nGRU = len(src.dimensions['gru'])
                        domain_area = domain_area = src['HRUarea'][:].sum()

                        GRU_area = domain_area/float(nGRU)            # mean GRU area in square meter
                        GRU_channel_length = np.sqrt(GRU_area/np.pi)  # mean GRU chennel length in meter

                        # (3) Calculate a-priori GammaScale = (GRU_channel_length/velocity)/GammaShape
                        v_priori = 1.0 # unit: m/s
                        param_value = (GRU_channel_length/v_priori)/shape_priori    

                    # Identify param dimension for param_name
                    if 'hru' in param_dims:
                        param_dim = 'hru'
                    elif 'gru' in param_dims:
                        param_dim = 'gru'
                    else:
                        print('Parameter %s does not have dimensions gru or hru in summa output.\n \
                        Check before moving forward.'%(param_name))
                        sys.exit()

                    # Create this param variable and fill value
                    dst.createVariable(param_name, 'float', param_dim, fill_value=np.nan) 
                    dst[param_name][:] = param_value


    
    # #### 6. Copy trialParamFile to get trialParamFile_priori
    shutil.copy2(trialParamFile_priori, trialParamFile);
