### Python script to use SNAP as InSAR processor for TSX/TDX processing compatible with StaMPS PSI processing
# Author: Jonas Ziemer, adapted from Jose Manuel Delgado Blasco (snap2stamps package)
# Date: 01/01/2023
# Version: 2.1, Python 3.9

# Step 1: unzip downloaded TSX scenes (.tar; .tar.gz)
# Step 2: preparing secondaries in folder structure
# Step 3: subset TSX scenes 
# Step 4: Coregistration 
# Step 5: Interferogram generation
# Step 6: StaMPS export


import os
import shutil
import sys
import glob
import subprocess
import shlex
import time
import configparser
import argparse
import warnings

warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='This script sorts the secondary SAR SLC images into folders')
parser.add_argument("--ProjFile","-F", type=str)

args = parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile = args.ProjFile


print(configfile)


config = configparser.ConfigParser()
config.read(configfile)
PROJECTFOLDER=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
print(PROJECTFOLDER)

bar_message='\n#####################################################################\n'


##############################################################################
######################## Slaves sortering in folders #########################
##############################################################################
# Folders involved in this processing step
logfolder=os.path.join(PROJECTFOLDER,'logs')
secondariesfolder=os.path.join(PROJECTFOLDER,'secondaries')

if not os.path.exists(logfolder):
                os.makedirs(logfolder)

errorlog=os.path.join(logfolder,'secondaries_proc_stderr.log')
outlog=os.path.join(logfolder,'secondaries_proc_stdout.log')
out_file = open(outlog, 'a')
err_file = open(errorlog, 'a')

timeStarted_global = time.time()
# Iterate trough all files in the secondariesfolder
for filename in os.listdir(secondariesfolder):
    if filename.startswith("TDX1_SAR__SSC______SM_S_SRA") or filename.startswith("TSX1_SAR__SSC______SM_S_SRA"): 
       print(os.path.join(secondariesfolder, filename))
       # Create name of the output secondaries folder
       head, tail = os.path.split(os.path.join(secondariesfolder, filename))
       print(tail[28:36])
       subdirectory=secondariesfolder + '/' + tail[28:36]
       if not os.path.exists(subdirectory):
           os.makedirs(subdirectory)
       # Create subdirectories
       source=os.path.join(secondariesfolder, filename)
       destination=os.path.join(subdirectory, tail)
       print('Moving '+source+' to '+ destination)
       shutil.move(source,destination)
    else:
        continue
timeDelta_global = time.time() - timeStarted_global
print('Finished preparation in ' + str(timeDelta_global) + ' seconds.\n')
