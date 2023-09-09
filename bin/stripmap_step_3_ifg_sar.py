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

parser = argparse.ArgumentParser(description='This script runs the Interferogram computation and TopoPhase removal')
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

extDEM=config['PROC_PARAMETERS'].get('EXTDEM')

CACHE=config['COMPUTING_RESOURCES'].get('CACHE')
CPU=config['COMPUTING_RESOURCES'].get('CPU')

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

######################################################################################
####################### TSX-SAR Interferogram generation #############################
######################################################################################
# Folders involved in this processing step
outputcoregfolder=os.path.join(PROJECT,'coreg')
outputifgfolder=os.path.join(PROJECT,'ifg')
logfolder=os.path.join(PROJECT,'logs')

if not os.path.exists(outputifgfolder):
                os.makedirs(outputifgfolder)
if not os.path.exists(logfolder):
                os.makedirs(logfolder)

outlog=os.path.join(logfolder,'ifg_proc_stdout.log')

# Original Snap graph and replaced Snap graph for Interferogram generation 
if extDEM=='':
    graphxml=os.path.join(GRAPH,'stripmap_Interferogram_TopoPhase.xml')
else:
    graphxml=os.path.join(GRAPH,'stripmap_Interferogram_TopoPhase_extDEM.xml')
print(graphxml)
graph2run=os.path.join(GRAPH,'ifg_2run.xml')

out_file = open(outlog, 'a')
err_file=out_file

# Processing layout
print(bar_message)
out_file.write(bar_message)
message='## Interferogram generation started:\n'
print(message)
out_file.write(message)
print(bar_message)
out_file.write(bar_message)
k=0
timeStarted_global = time.time()
# Iterate trough all files in the coregfolder
for dimfile in glob.iglob(outputcoregfolder + '/*.dim'):
    print(dimfile)
    k=k+1
    # Create name of the output ifg file
    head, tail = os.path.split(os.path.join(outputcoregfolder, dimfile))
    message='['+str(k)+'] Processing coreg file: '+tail+'\n'
    print(message)
    out_file.write(message)
    outputname=tail[0:17]+'.dim'
    with open(graphxml, 'r') as file :
       filedata = file.read()
    # Replace the target string and generate a new file with replaced names for use in SNAP
    filedata = filedata.replace('COREGFILE',dimfile)
    filedata = filedata.replace('EXTERNALDEM', extDEM)
    filedata = filedata.replace('OUTPUTIFGFOLDER',outputifgfolder)    
    filedata = filedata.replace('OUTPUTFILE',outputname)
    with open(graph2run, 'w') as file:
       file.write(filedata)
    args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
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
        message='Error computing with interferogram generation of coreg file '+str(dimfile)
        err_file.write(message+'\n')
    else:
        message='Interferogram computation for data '+str(outputname)+' successfully completed.\n'
        print(message)
        out_file.write(message)
    print(bar_message)
    out_file.write(bar_message)
timeDelta_global = time.time() - timeStarted_global
print('Finished interferogram generation in ' + str(timeDelta_global) + ' seconds.\n')
out_file.close()
