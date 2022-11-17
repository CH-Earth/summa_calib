## SUMMA parameter estimation

This repository provides four SUMMA parameter estimation (calibration) demos. The differences between demos are their parameter estimation tools and how they run the hydrologic model. The first two demos are good for all users. The last two demos are for users who are familiar with computer clusters and need to speed up SUMMA runs. 

| Demo   | Parameter estimation | Hydrologic model | 
|:-------|:---------------------|:-----------------|
| Demo1  | OSTRICH          | serial run                         |
| Demo2  | DDS Python code  | serial run                         |
| Demo3  | OSTRICH          | parallel run (a cluster job)       | 
| Demo4  | DDS Python code  | parallel run (a cluster job array) | 

### Parameter estimation tools

The demos show the use of two parameter estimation tools. Optimization Software Toolkit for Research Involving Computational Heuristics (OSTRICH) is a model independent optimization and parameter estimation tool (Matott, 2017). It contains a variety of optimization algorithms, including Dynamically Dimensioned Search (DDS) (Tolson and Shoemaker, 2007). DDS features finding good parameter solutions quickly and requiring no algorithm parameter tuning. 

The DDS Python code is provided to help users get out of OSTRICH. Often when a hydrological model is computationally expensive, using a single computer or a single cluster job to run the hydrological model requires unrealistically long queue time (if too many threads are requested) or elapsed time (if too few threads are requested). In this case, using the cluster job array (using more than one job) is a solution. This disables users from using OSTRICH. 

### Hydrologic model
The hydrologic model is for the Bow River at Banff, Canada, and is the same in all demos. It consists of the SUMMA hydrological model (Clark et al., 2015a,b) and the mizuRoute routing model (Mizukami et al., 2016). The hydrologic model provided is created by the Community Workflows to Advance Reproducibility in Hydrologic Modeling (CWARHM) (Knoben et al., 2022). For demonstration purpose, the model simulation period is only one month.

The serial and parallel runs described in the above table are for SUMMA only. Serial run processes all Group Response Units (GRUs) one after the other per time step. In contrast, parallel run splits all GRUs into subsets and runs SUMMA for the subsets at the same time. The GRUs included in the same subset are still processed one after the other per time step. 

### To get start
1. Obtain SUMMA and mizuRoute executables. In the [CWARHM repository](https://github.com/CH-Earth/CWARHM.git), the _2_install_ folder describes in detail how to download and install both.  <br/>

2. Obtain OSTRICH executable. If you are running Demo 1 or 3, obtain the OSTRICH executable that matches your operating system. Place it to the demo folder to replace the provided Ostrich.exe. The OSTRICH source code and executables can be downloaded from the [Ostrich website](https://www.eng.buffalo.edu/~lsmatott/Ostrich/OstrichMain.html).<br/>

3. Set required computational enviroment. The presented code is written in a combination of Bash and Python. It requires a few libraries and Python packages:

    - Bash: nco 
    - Python: numpy, xarray, netCDF4.

4. Fill in paths. Navigate to the demo folder, and fill in the following paths: 

    - control_active.txt: _<calib_path\>_, _<summa/exe/path\>_ and _<mizuroute/exe/path\>_
    - model/settings/SUMMA/fileManager.txt: _<model/directory/path\>_
    - model/settings/mizuRoute/mizuroute.control: _<model/directory/path\>_
    
5. Fill in job submission account. If you are running Demo 3 or 4 and using the SLURM job scheduler, please fill in your associated account name in your cluster system to get job resource allocation. 

    - demo3/run_Ostrich.sh: _<account\>_ 
    - demo4/run_DDS.sh: _<account\>_ 

    If you are using a job scheduler other than SLURM, you will need extra changes. In the above two files as well as _demo4/run_summa.sh_ and _demo4/run_route.sh_, change the SBATCH related commands to suit your job scheduler. You can easily find all the SBATCH related contents by searching for keyword "sbatch" in these files. If someone wants to contribute actual configure files, that would be appreciated. 

6. Run demos. Navigate to the demo folder, and run the parameter estimation. Taking the Linux system and the SLURM scheduler as an example, the specific run commands are:
    - demo1: ./run_Ostrich.sh 
    - demo2: ./run_DDS.sh
    - demo3: sbatch run_Ostrich.sh  &nbsp;(This submits one job)
    - demo4: ./run_DDS.sh           &nbsp;(This submits multiple depedent jobs)


Please look at [readthedocs](https://h294liu.github.io/summa_calib/) to learn more about SUMMA parameter estimation methodology and demo details.

### Acknowledgements
We thank our colleagues who have contributed to improving this repository (in order of contribution time):

- Hongli Liu
- Andy Wood
- Shawn Matott
- Martyn Clark
- Jim Freer
- Louise Arnal
- Guoqiang Tang
- Chris Marsh

We acknowledge that the presented DDS Python code is developed based on the code written by Thouheed A. Gaffoor at [https://github.com/t2abdulg/DDS_Py.git](https://github.com/t2abdulg/DDS_Py.git).

### References

Clark, M. P., B. Nijssen, J. D. Lundquist, D. Kavetski, D. E. Rupp, R. A. Woods, J. E. Freer, E. D. Gutmann, A. W. Wood, L. D. Brekke, J. R. Arnold, D. J. Gochis, R. M. Rasmussen, 2015a: A unified approach for process-based hydrologic modeling: Part 1. Modeling concept. Water Resources Research, [doi:10.1002/2015WR017198](https://doi.org/10.1002/2015WR017198)

Clark, M. P., B. Nijssen, J. D. Lundquist, D. Kavetski, D. E. Rupp, R. A. Woods, J. E. Freer, E. D. Gutmann, A. W. Wood, D. J. Gochis, R. M. Rasmussen, D. G. Tarboton, V. Mahat, G. N. Flerchinger, D. G. Marks, 2015b: A unified approach for process-based hydrologic modeling: Part 2. Model implementation and case studies. Water Resources Research, [doi:10.1002/2015WR017200](https://doi.org/10.1002/2015WR017200)

Knoben, W. J. M., Clark, M. P., Bales, J., Bennett, A., Gharari, S., Marsh, C. B., Nijssen, B., Pietroniro, A., Spiteri, R. J., Tarboton, D. G. & Wood, A. W. (2022). Community Workflows to Advance Reproducibility in Hydrologic Modeling: Separating model-agnostic and model-specific configuration steps in applications of large-domain hydrologic models. Water Resources Research, e2021WR031753. [doi: 10.1029/2021WR031753](https://doi.org/10.1029/2021WR031753)

Matott, LS. 2017. OSTRICH: an Optimization Software Tool, Documentation and User's Guide, Version 17.12.19. 79 pages, University at Buffalo Center for Computational Research, [www.eng.buffalo.edu/~lsmatott/Ostrich/OstrichMain.html](https://www.eng.buffalo.edu/~lsmatott/Ostrich/OstrichMain.html).

Mizukami, N., Clark, M. P., Sampson, K., Nijssen, B., Mao, Y., McMillan, H., Viger, R. J., Markstrom, S. L., Hay, L. E., Woods, R., Arnold, J. R., and Brekke, L. D., 2016: mizuRoute version 1: a river network routing tool for a continental domain water resources applications, Geosci. Model Dev., 9, 2223–2238, [doi:10.5194/gmd-9-2223-2016](https://doi.org/10.5194/gmd-9-2223-2016)

Tolson, B. A. and C. A. Shoemaker (2007), Dynamically dimensioned search algorithm for computationally efficient watershed model calibration, Water Resources Research, 43, W01413, [doi:10.1029/2005WR004723](https://doi.org/10.1029/2005WR004723).
