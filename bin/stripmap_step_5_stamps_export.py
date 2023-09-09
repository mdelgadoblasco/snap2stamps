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
from pathlib import Path
import sys
import glob
import subprocess
import shlex
import time
import warnings
import argparse
import configparser

warnings.filterwarnings('ignore')
sys.stdout.flush()

parser = argparse.ArgumentParser(description='This script runs the TerraSAR-X Interferogram computation and TopoPhase removal')
parser.add_argument("--ProjFile","-F", type=str)

args = parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile = args.ProjFile

bar_message='\n#####################################################################\n'

os.environ["LD_LIBRARY_PATH"] ="."
# Getting configuration variables from inputfile
config = configparser.ConfigParser()
config.read(configfile)

PROJECT=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
GRAPH=config['PROJECT_DEFINITION'].get('GRAPHSFOLDER')

OVERWRITE=config['PROC_OPTIONS'].get('OVERWRITE')
SMARTHDD=config['PROC_OPTIONS'].get('SMARTHDD')
CACHE=config['COMPUTING_RESOURCES'].get('CACHE')
CPU=config['COMPUTING_RESOURCES'].get('CPU')
MASTERFOLDER=config['PROC_PARAMETERS'].get('MASTER')
masterfolder=MASTERFOLDER

###################################################################
## GETTING PATH to gpt executable
SNAPFOLDER=config['SNAP_GPT'].get('SNAP_INSTALLATION_FOLDER')
GPT=os.path.join(SNAPFOLDER,'bin','gpt')
if os.name == 'nt':
    GPT=os.path.join(SNAPFOLDER,'bin','gpt.exe')

############################################################################
# Checking GPT
if not os.path.exists(GPT):
    errormessage="GPT executable not found in "+GPT+".Processing aborted"
    print(errormessage)
    sys.exit(errormessage)
###################################################################################
############################# StaMPS PSI export ###################################
###################################################################################
# Folders involved in this processing step
coregfolder=os.path.join(PROJECT,'coreg')
ifgfolder=os.path.join(PROJECT,'ifg')
head, tail = os.path.split(masterfolder)
outputexportfolder=os.path.join(PROJECT,'INSAR_'+tail[0:8])
logfolder=os.path.join(PROJECT,'logs')

if not os.path.exists(outputexportfolder):
                os.makedirs(outputexportfolder)
if not os.path.exists(logfolder):
                os.makedirs(logfolder)

outlog=os.path.join(logfolder,'export_proc_stdout.log')

# Original Snap graph and replaced Snap graph for subsettting
graphxml=os.path.join(GRAPH,'stripmap_Export.xml')
print(graphxml)
graph2run=os.path.join(GRAPH,'export2run.xml')

out_file = open(outlog, 'a')
err_file=out_file

# Processing layout
print(bar_message)
out_file.write(bar_message)
message='## StaMPS PSI export started:\n'
print(message)
out_file.write(message)
print(bar_message)
out_file.write(bar_message)
k=0
timeStarted_global = time.time()
# Iterate trough all files in the coreg- and ifg folder
for dimfile in glob.iglob(coregfolder + '/*.dim'):
    head, tail = os.path.split(os.path.join(coregfolder, dimfile))
    k=k+1
    message='['+str(k)+'] Exporting pair: master-secondary pair '+tail+'\n'
    ifgdim = Path(ifgfolder+'/'+tail)
    print(ifgdim)
    if ifgdim.is_file():
        print(message)
        out_file.write(message)
    with open(graphxml, 'r') as file:
        filedata = file.read()
    # Replace the target string and generate a new file with replaced names for use in SNAP
    filedata = filedata.replace('COREGFILE',dimfile)
    filedata = filedata.replace('IFGFILE',str(ifgdim))
    filedata = filedata.replace('OUTPUTFOLDER',outputexportfolder)
    with open(graph2run, 'w') as file:
            file.write(filedata)
    args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
    print(args)
    # Launch the processing
    process = subprocess.Popen(args, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    timeStarted = time.time()
    stdout = process.communicate()[0]
    print('SNAP STDOUT:{}'.format(stdout))
    # Get execution time
    timeDelta = time.time() - timeStarted                     
    print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
    out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
    if process.returncode != 0 :
       message='Error exporting '+str(tail)+'\n' 
       err_file.write(message)
    else:
       message='Stamps export of '+str(tail)+' successfully completed.\n'
       print(message)
       out_file.write(message)
    print(bar_message)
    out_file.write(bar_message)
timeDelta_global = time.time() - timeStarted_global
print('Finished Stamps export in ' + str(timeDelta_global) + ' seconds.\n')
out_file.close()
err_file.close()
