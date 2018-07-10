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
                if "IW1" in line:
                        IW = line.split('=')[1].strip()
                        print IW
                if "GRAPHSFOLDER" in line:
                        GRAPH = line.split('=')[1].strip()
                        print GRAPH
                if "GPTBIN_PATH" in line:
                        GPT = line.split('=')[1].strip()
                        print GPT
		if "CACHE" in line:
			CACHE = line.split('=')[1].strip()
		if "CPU" in line:
			CPU = line.split('=')[1].strip()
finally:
        in_file.close()

#############################################################################
### TOPSAR Splitting (Assembling) and Apply Orbit section ####
############################################################################
slavefolder=PROJECT+'/slaves'
splitfolder=PROJECT+'/split'
logfolder=PROJECT+'/logs'
graphfolder=PROJECT+'/graphs'
if not os.path.exists(splitfolder):
                os.makedirs(splitfolder)
if not os.path.exists(logfolder):
                os.makedirs(logfolder)
if not os.path.exists(graphfolder):
                os.makedirs(graphfolder)

graph2run=PROJECT+'/graphs/splitgraph2run.xml'
outlog=logfolder+'/split_proc_stdout.log'
out_file = open(outlog, 'a')
err_file=out_file

print bar_message
out_file.write(bar_message)
message='## TOPSAR Splitting and Apply Orbit\n'
print message
out_file.write(message)
print bar_message
out_file.write(bar_message)
k=0
for acdatefolder in sorted(os.listdir(slavefolder)):
    k=k+1
    print '['+str(k)+'] Folder: '+acdatefolder
    out_file.write('['+str(k)+'] Folder: '+acdatefolder+'\n')
    print os.path.join(slavefolder, acdatefolder)
    out_file.write(str(os.path.join(slavefolder, acdatefolder))+'\n')
    files = glob.glob(os.path.join(slavefolder, acdatefolder) + '/*.zip')
    print files
    out_file.write(str(files)+'\n')
    head, tail = os.path.split(os.path.join(str(files)))
    splitslavefolder=splitfolder+'/'+tail[17:25]
    if not os.path.exists(splitslavefolder):
                os.makedirs(splitslavefolder)
    outputname=tail[17:25]+'_'+IW+'.dim'
    if len(files) == 1 :
	graphxml=GRAPH+'/slave_split_applyorbit.xml'
       # Read in the file
        print 'FILE(s) : '+files[0]
        with open(graphxml, 'r') as file :
           filedata = file.read()
        # Replace the target string
        filedata = filedata.replace('INPUTFILE', files[0])
	filedata = filedata.replace('IWs',IW)
	filedata = filedata.replace('OUTPUTFILE',splitslavefolder+'/'+outputname)
       # # Write the file out again
        with open(graph2run, 'w') as file:
           file.write(filedata)
    if len(files) > 1 :
	graphxml=GRAPH+'/slaves_assemble_split_applyorbit.xml'
        with open(graphxml, 'r') as file :
           filedata = file.read()
        # Replace the target string
        filedata = filedata.replace('INPUTFILE1', files[0])
	filedata = filedata.replace('INPUTFILE2', files[1])
	filedata = filedata.replace('IWs',IW)
	filedata = filedata.replace('OUTPUTFILE',splitslavefolder+'/'+outputname)
        # Write the file out again
        with open(graph2run, 'w') as file:
           file.write(filedata)

    args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
    print args
    out_file.write(str(args)+'\n')
    # launching the process
    process = subprocess.Popen(args, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    timeStarted = time.time()
    stdout = process.communicate()[0]
    print 'SNAP STDOUT:{}'.format(stdout)
    timeDelta = time.time() - timeStarted                     # Get execution time.
    print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
    out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
    if process.returncode != 0 :
	message='Error splitting slave '+str(files)
	err_file.write(message)
    else: 
	message='Split slave '+str(files)+' successfully completed.\n'
	print message
	out_file.write(message)
    print bar_message
    out_file.write(bar_message)
out_file.close()
