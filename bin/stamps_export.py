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

###################################################################################
##### StaMPS PSI export ##################
###################################################################################
coregfolder=PROJECT+'/coreg'
ifgfolder=PROJECT+'/ifg'
outputexportfolder=PROJECT+'/export-PSI'
logfolder=PROJECT+'/logs'

if not os.path.exists(outputexportfolder):
                os.makedirs(outputexportfolder)
if not os.path.exists(logfolder):
                os.makedirs(logfolder)

outlog=logfolder+'/export_proc_stdout.log'
out_file = open(outlog, 'a')
err_file=out_file
graphxml=GRAPH+'/export.xml'
graph2run=GRAPH+'/export2run.xml'
print bar_message
out_file.write(bar_message)
message='## StaMPS PSI export started:\n'
print message
out_file.write(message)
print bar_message
out_file.write(bar_message)
k=0
for dimfile in glob.iglob(coregfolder + '/*'+IW+'.dim'):
    head, tail = os.path.split(os.path.join(coregfolder, dimfile))
    k=k+1
    message='['+str(k)+'] Exporting pair: master-slave pair '+tail+'\n'
    ifgdim = Path(ifgfolder+'/'+tail)
    print ifgdim
    if ifgdim.is_file():
        print message
        out_file.write(message)
	with open(graphxml, 'r') as file :
           filedata = file.read()
        # Replace the target string
	filedata = filedata.replace('COREGFILE',dimfile)
	filedata = filedata.replace('IFGFILE', str(ifgdim))
	filedata = filedata.replace('OUTPUTFOLDER',outputexportfolder)
	# Write the file out again
	with open(graph2run, 'w') as file:
           file.write(filedata)
        args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
	print args
	# Launching process
        process = subprocess.Popen(args, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	timeStarted = time.time()
        stdout = process.communicate()[0]
        print 'SNAP STDOUT:{}'.format(stdout)
        timeDelta = time.time() - timeStarted                     # Get execution time.
        print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
	out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
        if process.returncode != 0 :
           message='Error exporting '+str(tail)+'\n' 
           err_file.write(message)
        else:
           message='Stamps export of '+str(tail)+' successfully completed.\n'
           print message
           out_file.write(message)
	print bar_message
	out_file.write(bar_message)
out_file.close()
err_file.close()
