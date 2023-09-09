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
import tarfile

import configparser
import argparse
import warnings

warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='This script unpacks the original TSX/TDX data')
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
################### Unpack zipped files in the zipfolder ##################### 
##############################################################################
# Folders involved in this processing step
logfolder=os.path.join(PROJECTFOLDER,'logs')
zipfolder=os.path.join(PROJECTFOLDER,'zipfiles')
secondariesfolder=os.path.join(PROJECTFOLDER,'secondaries')

if not os.path.exists(logfolder):
                os.makedirs(logfolder)
if not os.path.exists(zipfolder):
                os.makedirs(zipfolder)
if not os.path.exists(secondariesfolder):
                os.makedirs(secondariesfolder)
                
errorlog=os.path.join(logfolder,'unpack_proc_stderr.log')
outlog=os.path.join(logfolder,'unpack_proc_stdout.log')
out_file = open(outlog, 'a')
err_file = open(errorlog, 'a')

timeStarted_global = time.time()
# Unpack .tar(.gz) files
try:
    for filename in os.listdir(zipfolder):
        os.chdir(zipfolder)
        filename = zipfolder + '/' + filename
        print(filename)
        if filename.endswith("tar.gz"):
            tar = tarfile.open(filename, "r:gz")
            if filename.endswith("tar"):
                tar = tarfile.open(filename, "r:")
        elif filename.endswith("tar"):
            tar = tarfile.open(filename, "r:")
        tar.extractall()
        tar.close()
except:
    raise Exception("The files have already been extracted!")

# Cut out the data folder only, to get the right naming of the files for later processing steps
for file in os.listdir(zipfolder):
    folder = os.path.join(zipfolder, file)
    if os.path.isdir(folder):
        for tsxmainfolder in glob.iglob(folder + '/*'):
            if tsxmainfolder.endswith('.L1B'):
                for tsxsubfolder in glob.iglob(tsxmainfolder + '/*'):
                    print(tsxsubfolder)
                    shutil.move(tsxsubfolder, secondariesfolder)
timeDelta_global = time.time() - timeStarted_global
print('Finished unzipping in ' + str(timeDelta_global) + ' seconds.\n')
