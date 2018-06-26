### Python script to use SNAP as InSAR processor compatible with StaMPS PSI processing
# Author Jose Manuel Delgado Blasco
# Date: 21/06/2018
# Version: 1.0

# Step 1 : preparing slaves in folder structure
# Step 2 : TOPSAR Splitting (Assembling) and Apply Orbit
# Step 3 : Coregistration and Interferogram generation
# Step 4 : StaMPS export

# Added option for CACHE and CPU specification by user
# Planned support for DEM selection and ORBIT type selection 


import os
from pathlib import Path
import shutil
import sys
import glob
import subprocess
import shlex
import time
inputfile = sys.argv[1]

bar_message='\n#####################################################################\n'

# Getting configuration variables from inputfile
try:
        in_file = open(inputfile, 'r')
        for line in in_file.readlines():
                if "PROJECTFOLDER" in line:
                        PROJECT = line.split('=')[1].strip()
                        print PROJECT
finally:
        in_file.close()

##############################################################################
#### Slaves sortering in folders ########################
##############################################################################
logfolder=PROJECT+'/logs'
if not os.path.exists(logfolder):
                os.makedirs(logfolder)
errorlog=logfolder+'/split_proc_stderr.log'
outlog=logfolder+'/split_proc_stdout.log'

out_file = open(outlog, 'a')
err_file = open(errorlog, 'a')

directory=PROJECT+'/slaves'
for filename in os.listdir(directory):
    if filename.endswith(".zip") : 
       print(os.path.join(directory, filename))
       head, tail = os.path.split(os.path.join(directory, filename))
       print tail[17:25]
       subdirectory=directory+'/'+tail[17:25]
       if not os.path.exists(subdirectory):
		os.makedirs(subdirectory)
       #### Moving files
       source=os.path.join(directory, filename)
       destination=os.path.join(subdirectory, tail)
       print 'Moving '+source+' to '+destination
       shutil.move(source,destination)
    else:
        continue
