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
projectfolder=PROJECTFOLDER
print(PROJECTFOLDER)

bar_message='\n#####################################################################\n'


##############################################################################
######################## Slaves sortering in folders #########################
##############################################################################
# Folders involved in this processing step
logfolder=os.path.join(PROJECTFOLDER,'logs')
subsetfolder=os.path.join(PROJECTFOLDER,'subset')

if not os.path.exists(logfolder):
                os.makedirs(logfolder)

errorlog=os.path.join(logfolder,'masterselect_proc_stderr.log')
outlog=os.path.join(logfolder,'masterselect_proc_stdout.log')
out_file = open(outlog, 'a')
err_file = open(errorlog, 'a')

timeStarted_global = time.time()
masterfolder=projectfolder + '/master'
if not os.path.exists(masterfolder):
    os.makedirs(masterfolder)
# Select master 
date = input("Enter the date of the masterscene in the format 'yyyymmdd' (Dont forget to specify the selected master file (yyyymmdd_sub.dim) in the project_stripmap.conf file (line 17)!):")
# Forward the input to the autorun script
sys.stdout.write(date)
items = []
# Get a list of all items in the directory
items = os.listdir(subsetfolder)

# Find the items containing the selected date and move them to the "master" folder
for item in items:
    if date in item:
        item_path = os.path.join(subsetfolder, item)
        shutil.move(item_path, masterfolder)
        print(f"Moved '{item}' to 'master' folder.")
timeDelta_global = time.time() - timeStarted_global
print('Finished preparation in ' + str(timeDelta_global) + ' seconds.\n')
