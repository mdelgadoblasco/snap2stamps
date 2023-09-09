import os
from pathlib import Path
import sys
import glob
from subprocess import PIPE, Popen, STDOUT
import shlex
import time
import shutil

import configparser
import warnings
import argparse

import re
from datetime import datetime
from collections import defaultdict


sys.stdout.flush()
warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='This script create PNG files from each data with the options split/coreg/ifg')
parser.add_argument("--ProjFile","-F", type=str)
parser.add_argument("--Mode","-M", type=str)

args = parser.parse_args()

def usage():
    message='####################################################\n'
    message=message+'Usage: python '+sys.argv[0]+' -F [project.conf] -M [mode] \n'
    message=message+'               project.conf file\n'
    message=message+'               mode : split/coreg/ifg\n'
    message=message+'All parameters mandatory'
    return message

if not args.ProjFile:
    print("No Input File detected")
    print(usage())
    sys.exit(-1)
else:
    configfile = args.ProjFile
if not args.Mode:
    print('No Mode selected')
    print(usage())
    sys.exit(-1)
else:
    mode=args.Mode

bar_message='\n#####################################################################\n'
# Setting LD_LIBRARY_PATH for SNAP
os.environ["LD_LIBRARY_PATH"] = "."

# Getting configuration variables from inputfile
config = configparser.ConfigParser()
config.read(configfile)

PROJECT=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
GRAPH=config['PROJECT_DEFINITION'].get('GRAPHSFOLDER')

OVERWRITE=config['PROC_OPTIONS'].get('OVERWRITE')
SMARTHDD=config['PROC_OPTIONS'].get('SMARTHDD')

POLARISATION=config['PROC_PARAMETERS'].get('POLARISATION')
MASTER=config['PROC_PARAMETERS'].get('MASTERFOLDER')

CACHE=config['COMPUTING_RESOURCES'].get('CACHE')
CPU=config['COMPUTING_RESOURCES'].get('CPU')

###################################################################
## GETTING PATH to gpt executable
SNAPFOLDER=config['SNAP_GPT'].get('SNAP_INSTALLATION_FOLDER')
GPT=os.path.join(SNAPFOLDER,'bin','gpt')
PCONVERT=os.path.join(SNAPFOLDER,'bin','pconvert')
if os.name == 'nt':
    GPT=os.path.join(SNAPFOLDER,'bin','gpt.exe')
    PCONVERT=os.path.join(SNAPFOLDER,'bin','pconvert.exe')
#sys.exit()

SNAPHIDDEN=config['SNAP_GPT'].get('SNAP_HOME_DIR')
PALETTES=os.path.join(SNAPHIDDEN,'auxdata','color_palettes')

##################################################################################
# Checking GPT
if not os.path.exists(GPT) or not os.path.exists(PCONVERT):
    errormessage="GPT or PCONVERT executable not found in "+os.path.dirname(GPT)+".Processing aborted"
    print(errormessage)
    sys.exit(errormessage)

######################################################################################
## Plotting secondaries amplitude and Interferometric phase ##
######################################################################################
# Initializing set-up
secondariesplittedfolder=os.path.join(PROJECT,'subset')
masterfolder=os.path.join(PROJECT,'master')
coregfolder=os.path.join(PROJECT,'coreg')
ifgfolder=os.path.join(PROJECT,'ifg')
graphfolder=os.path.join(PROJECT,'graphs')
logfolder=os.path.join(PROJECT,'logs')
plotfolder=os.path.join(PROJECT,'plot_'+mode)

if not os.path.exists(graphfolder):
        os.makedirs(graphfolder)
if not os.path.exists(logfolder):
        os.makedirs(logfolder)
if not os.path.exists(plotfolder):
	os.makedirs(plotfolder)

outlog=logfolder+'/plot_stdout.log'

### Conversion of SNAPs date format, only needed for coreg and ifg plotting
output_format = "%d%b%Y"  # Desired output format
date_list = []

if mode == 'coreg':
    for subdir in os.listdir(coregfolder):
        subdir_path = os.path.join(coregfolder, subdir)
        if os.path.isdir(subdir_path):
            mst_date = subdir.split("_")[0]
            slv_dates = subdir.split("_")[1].split(".")[0]  # Extract the second date part from subdirectory name
            try:
                mst_date_obj = datetime.strptime(mst_date, "%Y%m%d")
                formatted_mst_date = mst_date_obj.strftime(output_format)
                slv_date_obj = datetime.strptime(slv_dates, "%Y%m%d")
                formatted_slv_dates = slv_date_obj.strftime(output_format)
                date_list.append(formatted_slv_dates)
            except ValueError:
                print(f"Error converting date in {subdir}: {dates}")
if mode == 'ifg':
    for subdir in os.listdir(ifgfolder):
        subdir_path = os.path.join(ifgfolder, subdir)
        if os.path.isdir(subdir_path):
            mst_date = subdir.split("_")[0]
            slv_dates = subdir.split("_")[1].split(".")[0]  # Extract the second date part from subdirectory name
            try:
                mst_date_obj = datetime.strptime(mst_date, "%Y%m%d")
                formatted_mst_date = mst_date_obj.strftime(output_format)
                slv_date_obj = datetime.strptime(slv_dates, "%Y%m%d")
                formatted_slv_dates = slv_date_obj.strftime(output_format)
                date_list.append(formatted_slv_dates)
            except ValueError:
                print(f"Error converting date in {subdir}: {dates}")

           
out_file = open(outlog, 'a')
err_file=out_file

print(bar_message)
out_file.write(bar_message)
message='## Plotting secondaries amplitude and Interferometric phase started:\n'
print(message)
out_file.write(message)
print(bar_message)
out_file.write(bar_message)

if mode == 'split':
    searchfolder = secondariesplittedfolder
elif mode == 'coreg':
    searchfolder = coregfolder
elif mode == 'ifg':
    searchfolder = ifgfolder

ibandlist = []
qbandlist = []

# Create the QBAND and IBAND names for the XML plot2run file
for formatted_slv_dates, dimfile in zip(date_list, sorted(glob.iglob(searchfolder + '/*' + '.dim'))):
    if mode == 'coreg':
        graphxml = GRAPH + '/stripmap_plot_coreg.xml'
        searchfolder = coregfolder
        ibandname = 'i_*' + POLARISATION + '_slv1_' + formatted_slv_dates
        ibandlist.append(ibandname)
        qbandname = 'q_*' + POLARISATION + '_slv1_' + formatted_slv_dates
        qbandlist.append(qbandname)
    if mode == 'ifg':
        graphxml = GRAPH + '/stripmap_plot_ifg.xml'
        searchfolder = ifgfolder
        ibandname = 'i_ifg_*'+POLARISATION+'_'+formatted_mst_date+'_'+formatted_slv_dates
        ibandlist.append(ibandname)
        qbandname = 'q_ifg_*'+POLARISATION+'_'+formatted_mst_date+'_'+formatted_slv_dates
        qbandlist.append(qbandname)
        
    graph2run = graphfolder + '/plot2run_' + mode + '.xml'

# Execute plotting for the SLC subsets (simple QBAND and IBAND names)
if mode == 'split':
    graphxml = GRAPH + '/stripmap_plot_split.xml'
    searchfolder = secondariesplittedfolder
    ibandname = 'i_*' + POLARISATION
    qbandname = 'q_*' + POLARISATION
    graph2run = graphfolder + '/plot2run_' + mode + '.xml'
    k=0
    for dimfile in sorted(glob.iglob(searchfolder + '/*'+'.dim')):
        print (dimfile)
        k=k+1
        head, tail = os.path.split(os.path.join(searchfolder, dimfile))
        message='['+str(k)+'] Processing file :'+tail+'\n'
        print( message)
        out_file.write(message)
        outputname=tail[:-4]+'_'+mode
        print(searchfolder+'/'+tail[:-3]+'data/'+ibandname+'*img')
        iband=glob.glob(searchfolder+'/'+tail[:-3]+'data/'+ibandname+'*.img')
        iband=os.path.basename(iband[0])
        iband=iband.split('.')[0]
        qband=glob.glob(searchfolder+'/'+tail[:-3]+'data/'+qbandname+'*.img')
        qband=os.path.basename(qband[0])
        qband=qband.split('.')[0]
        with open(graphxml, 'r') as file :
            filedata = file.read()
                # Replace the target string
        filedata = filedata.replace('INPUTFILE', dimfile)
        filedata = filedata.replace('OUTPUTFOLDER',plotfolder)
        filedata = filedata.replace('OUTPUTNAME',outputname)
        filedata = filedata.replace('IBAND',iband)
        filedata = filedata.replace('QBAND',qband)
        # Write the file out again
        with open(graph2run, 'w') as file:
            file.write(filedata)
        args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
        # Check if exists
        print(plotfolder+'/'+outputname+'.dim')
        if not os.path.exists(str(plotfolder+'/'+outputname+'.png')) and OVERWRITE=='N':
            # Launch the processing         
            print('Creating file :'+outputname+'.dim')
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(str(line))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error creating png of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='Aux file of '+str(tail)+' successfully generated.\n'
            print (message)
            out_file.write(message)
        ## CONVERTING TO PNG
            inputfile=plotfolder+'/'+outputname+'.dim'
            args=[PCONVERT,'-b','1','-f','png','-o',plotfolder,inputfile]
            print(args)
            # Launch the processing         
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(str(line))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error creating png of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='PNG of '+str(tail)+' successfully completed.\n'
                print('Removing tmp file :'+inputfile)
                os.remove(inputfile)
                shutil.rmtree(inputfile[:-3]+'data')
            print (message)
            out_file.write(message)
        else:
            message="File :"+outputname+" already exists. Processing skipped"
            print(message)
            print(bar_message)
            out_file.write(message)
        out_file.write(bar_message)

# Execute plotting for the coregistered products and/or the interferograms (complex QBAND and IBAND names)            
if mode == 'coreg':
    graphxml = GRAPH + '/stripmap_plot_coreg.xml'
    searchfolder = coregfolder
    ibandname = 'i_*' + POLARISATION + '_slv1_' + formatted_slv_dates
    ibandlist.append(ibandname)
    qbandname = 'q_*' + POLARISATION + '_slv1_' + formatted_slv_dates
    qbandlist.append(qbandname)
    graph2run = graphfolder + '/plot2run_' + mode + '.xml'
    for k, (dimfile, ibandname, qbandname) in enumerate(zip(sorted(glob.iglob(searchfolder + '/*' + '.dim')), ibandlist, qbandlist), start=1):
        print(dimfile)
        head, tail = os.path.split(os.path.join(searchfolder, dimfile))
        message = '[' + str(k) + '] Processing file :' + tail + '\n'
        print(message)
        out_file.write(message)
        outputname = tail[:-4] + '_' + mode
        print(searchfolder + '/' + tail[:-3] + 'data/' + ibandname + '*img')
        iband_list = glob.glob(searchfolder + '/' + tail[:-3] + 'data/' + ibandname + '*.img')
        iband_names = []
        for iband_file in iband_list:
            iband = os.path.basename(iband_file).split('.')[0]
        qband_list = glob.glob(searchfolder + '/' + tail[:-3] + 'data/' + qbandname + '*.img')
        qband_names = []
        for qband_file in qband_list:
            qband = os.path.basename(qband_file).split('.')[0]
        with open(graphxml, 'r') as file :
            filedata = file.read()
        # Replace the target string
        filedata = filedata.replace('INPUTFILE', dimfile)
        filedata = filedata.replace('OUTPUTFOLDER',plotfolder)
        filedata = filedata.replace('OUTPUTNAME',outputname)
        filedata = filedata.replace('IBAND',iband)
        filedata = filedata.replace('QBAND',qband)      
        # Write the file out again
        with open(graph2run, 'w') as file:
            file.write(filedata)
        args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
        # Check if exists
        print(plotfolder+'/'+outputname+'.dim')
        if not os.path.exists(str(plotfolder+'/'+outputname+'.png')) and OVERWRITE=='N':
            # Launch the processing         
            print('Creating file :'+outputname+'.dim')
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(str(line))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error creating png of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='Aux file of '+str(tail)+' successfully generated.\n'
            print (message)
            out_file.write(message)
        ## CONVERTING TO PNG
            inputfile=plotfolder+'/'+outputname+'.dim'
            args=[PCONVERT,'-b','1','-f','png','-o',plotfolder,inputfile]
            print(args)
            # Launch the processing         
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(str(line))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error creating png of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='PNG of '+str(tail)+' successfully completed.\n'
                print('Removing tmp file :'+inputfile)
                os.remove(inputfile)
                shutil.rmtree(inputfile[:-3]+'data')
            print (message)
            out_file.write(message)
        else:
            message="File :"+outputname+" already exists. Processing skipped"
            print(message)
            print(bar_message)
            out_file.write(message)
        out_file.write(bar_message)
         
if mode == 'ifg':
    graphxml = GRAPH + '/stripmap_plot_ifg.xml'
    searchfolder = ifgfolder
    ibandname = 'i_ifg_*'+POLARISATION+'_'+formatted_mst_date+'_'+formatted_slv_dates
    ibandlist.append(ibandname)
    qbandname = 'q_ifg_*'+POLARISATION+'_'+formatted_mst_date+'_'+formatted_slv_dates
    qbandlist.append(qbandname)
    graph2run = graphfolder + '/plot2run_' + mode + '.xml'
    for k, (dimfile, ibandname, qbandname) in enumerate(zip(sorted(glob.iglob(searchfolder + '/*' + '.dim')), ibandlist, qbandlist), start=1):
        print(dimfile)
        head, tail = os.path.split(os.path.join(searchfolder, dimfile))
        message = '[' + str(k) + '] Processing file :' + tail + '\n'
        print(message)
        out_file.write(message)
        outputname = tail[:-4] + '_' + mode
        print(searchfolder + '/' + tail[:-3] + 'data/' + ibandname + '*img')
        iband_list = glob.glob(searchfolder + '/' + tail[:-3] + 'data/' + ibandname + '*.img')
        iband_names = []
        for iband_file in iband_list:
            iband = os.path.basename(iband_file).split('.')[0]
        qband_list = glob.glob(searchfolder + '/' + tail[:-3] + 'data/' + qbandname + '*.img')
        qband_names = []
        for qband_file in qband_list:
            qband = os.path.basename(qband_file).split('.')[0]
        with open(graphxml, 'r') as file :
            filedata = file.read()
        # Replace the target string
        filedata = filedata.replace('INPUTFILE', dimfile)
        filedata = filedata.replace('OUTPUTFOLDER',plotfolder)
        filedata = filedata.replace('OUTPUTNAME',outputname)
        filedata = filedata.replace('IBAND',iband)
        filedata = filedata.replace('QBAND',qband)      
        # Write the file out again
        with open(graph2run, 'w') as file:
            file.write(filedata)
        args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
        # Check if exists
        print(plotfolder+'/'+outputname+'.dim')
        if not os.path.exists(str(plotfolder+'/'+outputname+'.png')) and OVERWRITE=='N':
            # Launch the processing         
            print('Creating file :'+outputname+'.dim')
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(str(line))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error creating png of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='Aux file of '+str(tail)+' successfully generated.\n'
            print (message)
            out_file.write(message)
        ## CONVERTING TO PNG
            inputfile=plotfolder+'/'+outputname+'.dim'
            args=[PCONVERT,'-b','1','-f','png','-o',plotfolder,inputfile]
            print(args)
            # Launch the processing         
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(str(line))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error creating png of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='PNG of '+str(tail)+' successfully completed.\n'
                print('Removing tmp file :'+inputfile)
                os.remove(inputfile)
                shutil.rmtree(inputfile[:-3]+'data')
            print (message)
            out_file.write(message)
        else:
            message="File :"+outputname+" already exists. Processing skipped"
            print(message)
            print(bar_message)
            out_file.write(message)
        out_file.write(bar_message)
out_file.close()