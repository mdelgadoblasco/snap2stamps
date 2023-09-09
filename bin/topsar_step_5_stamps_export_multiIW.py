### Python script to use SNAP as InSAR processor compatible with StaMPS PSI processing
# Author Jose Manuel Delgado Blasco
# Date: 21/06/2018
# Updated: 01/04/2020
# Version: 2.0

# Step 0 : preparing secondaries in folder structure
# Step 1 : Master TOPSAR Splitting (Assembling) and Apply Orbit
# Step 2 : TOPSAR Splitting (Assembling) and Apply Orbit
# Step 3 : Coregistration and Interferogram generation
# Step 4 (optional): Plotting splitted and coregistered secondaries and interferometric phase
# Step 5 : StaMPS export

# Added in version 1.0
## Option for CACHE and CPU specification by user
# Added in version 2.0
## Automatic Master splitting
## Slave TOPSAR Splitting based on BBOX coordinates (LATMIN, LONMIN, LATMAX, LONMAX)
## Multi-Subswath support (merging prior StaMPS export)
## Convertion from shapefile to BBOX coordinates
## Option for disk space optimisation
## Option for overwrite or skip existing files
## Plotting scripts (secondaries and interferograms)
# Planned support for DEM selection and ORBIT type selection 

import configparser
import argparse
import warnings
import io
import os
from pathlib import Path
import sys
import glob
from subprocess import PIPE, Popen, STDOUT
import shlex
import time
import numpy as np
import geopandas as gpd
import shutil

sys.stdout.flush()
inputfile = sys.argv[1]
warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='This script splits the master Sentinel-1 image')
parser.add_argument("--ProjFile","-F", type=str)

args = parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile = args.ProjFile


bar_message='\n#####################################################################\n'
# Setting LD_LIBRARY_PATH for SNAP
#os.environ["LD_LIBRARY_PATH"] = os.getcwd()
os.environ["LD_LIBRARY_PATH"] = "."


config = configparser.ConfigParser()
config.read(configfile)

PROJECT=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
GRAPH=config['PROJECT_DEFINITION'].get('GRAPHSFOLDER')

OVERWRITE=config['PROC_OPTIONS'].get('OVERWRITE')
SMARTHDD=config['PROC_OPTIONS'].get('SMARTHDD')

MASTER=config['PROC_PARAMETERS'].get('MASTERFOLDER')
extDEM=config['PROC_PARAMETERS'].get('EXTDEM')

CACHE=config['COMPUTING_RESOURCES'].get('CACHE')
CPU=config['COMPUTING_RESOURCES'].get('CPU')

#########################################################
## GETTING AOI DEFINITION
aoi_mode=config['AOI_DEFINITION'].get('AOI_MODE')
print(aoi_mode)
if aoi_mode == 'WKT':
    polygon=config['AOI_DEFINITION'].get('WKT')
elif aoi_mode == 'BBOX':
    LONMIN=config['AOI_DEFINITION'].get('LONMIN')
    LATMIN=config['AOI_DEFINITION'].get('LATMIN')
    LONMAX=config['AOI_DEFINITION'].get('LONMAX')
    LATMAX=config['AOI_DEFINITION'].get('LATMAX')
    polygon='POLYGON (('+LONMIN+' '+LATMIN+','+LONMAX+' '+LATMIN+','+LONMAX+' '+LATMAX+','+LONMIN+' '+LATMAX+','+LONMIN+' '+LATMIN+'))'
elif aoi_mode == 'SHP' or aoi_mode == 'GeoJSON' or aoi_mode == 'KML':
    AOIFile=config['AOI_DEFINITION'].get('AOI_FILE')
    if aoi_mode != 'KML':
        gdf=gpd.read_file(AOIFile)
    else:
        import fiona
        fiona.drvsupport.supported_drivers['KML'] = 'rw'
        gdf = gpd.read_file(AOIFile, driver='KML')
        #polygon=str(gdf['geometry'].wkt)
    from shapely import wkt
    polygon = wkt.dumps(gdf['geometry'][0])
    polygon = str(gdf.envelope[0])
#    print(polygon)
else:
    print('Wrong AOI_MODE parameter! Please revise the configuration file')
    sys.exit()
    
print( polygon)

###################################################################
## GETTING PATH to gpt executable
SNAPFOLDER=config['SNAP_GPT'].get('SNAP_INSTALLATION_FOLDER')
GPT=os.path.join(SNAPFOLDER,'bin','gpt')
if os.name == 'nt':
        GPT=os.path.join(SNAPFOLDER,'bin','gpt.exe')

###################################################################################
# Checking GPT
if not os.path.exists(GPT):
    errormessage="GPT executable not found in "+GPT+".Processing aborted"
    print(errormessage)
    sys.exit(errormessage)


###################################################################################
##### StaMPS PSI export ##################
###################################################################################
masterfolder=os.path.join(PROJECT,'MasterSplit')
coregfolder=os.path.join(PROJECT,'coreg')
ifgfolder=os.path.join(PROJECT,'ifg')
graphfolder=os.path.join(PROJECT,'graphs')
logfolder=os.path.join(PROJECT,'logs')
masters=sorted(glob.glob(masterfolder+'/*dim'))
MASTER=masters[0]
head, tail = os.path.split(MASTER)
#outputexportfolder=PROJECT+'/INSAR_'+tail[17:25]
outputexportfolder=os.path.join(PROJECT,'INSAR_'+tail[0:8])

if not os.path.exists(outputexportfolder):
                os.makedirs(outputexportfolder)
if not os.path.exists(logfolder):
                os.makedirs(logfolder)

outlog=os.path.join(logfolder,'export_proc_stdout.log')
out_file = open(outlog, 'a')
err_file=out_file
graph2run=os.path.join(graphfolder,'export2run.xml')
print( bar_message)
out_file.write(bar_message)
message='## StaMPS PSI export started:\n'
print( message)
out_file.write(message)
print( bar_message)
out_file.write(bar_message)
k=0

masters=sorted(glob.glob(masterfolder+'/*dim'))
if len(masters)==1:
    graphxml=os.path.join(GRAPH,'topsar_export.xml')
else:
    graphxml=os.path.join(GRAPH,'topsar_export_mergeIW_subset.xml')
    if extDEM!='':
        graphxml=graphxml[:-4]+'_extDEM.xml'
#IW=masters[-7:-4]
#print(IW)
pairs=[]
for dimfile in sorted(glob.iglob(coregfolder + '/*.dim')):
	head, tail = os.path.split(os.path.join(coregfolder, dimfile))
	k=k+1
	pair=tail[0:17]
#	print(pair)
	pairs.append(pair)
pairs=np.unique(pairs)
#print(pairs)

dimfile=None
ifgdim=None
k=0
for pair in pairs:
    k=k+1
    dimfiles=sorted(glob.iglob(coregfolder+'/'+pair+'*.dim'))
    message='['+str(k)+'] Exporting pair: master-secondary pair '+pair+'\n'
    ifgdims = sorted(glob.iglob(ifgfolder+'/'+pair+'*.dim'))
    print(dimfiles)
    print( ifgdims)
	#dimfile.append(dimfiles)
	#ifgdim.append(ifgdims)
    for m in range(0,len(dimfiles)):
        if m==0:
            dimfile=dimfiles[m]
            ifgdim=ifgdims[m]
        else:
            dimfile=dimfile+','+dimfiles[m]
            ifgdim=ifgdim+','+ifgdims[m]
    print('Coreg and ifg files:')
    print(dimfile)
    print(ifgdim)
    print( message)
    out_file.write(message)
    with open(graphxml, 'r') as file :
        filedata = file.read()
    # Replace the target string
    filedata = filedata.replace('COREGFILE',dimfile)
    filedata = filedata.replace('IFGFILE', str(ifgdim))
    filedata = filedata.replace('OUTPUTFOLDER',outputexportfolder)
    filedata = filedata.replace('EXTERNALDEM',extDEM)
    filedata = filedata.replace('POLYGON',polygon)
    # Write the file out again
    with open(graph2run, 'w') as file:
        file.write(filedata)
    args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
    print( args)
    # Launching process
    timeStarted = time.time()
###	process = subprocess.Popen(args, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
###	process.wait()
#	timeStarted = time.time()
###	stdout = process.communicate()[0]
###	print( 'SNAP STDOUT:{}'.format(stdout).decode('utf-8'))
    process = Popen(args,  bufsize=1, stdout=PIPE, stderr=STDOUT)
    r = b""
    for line in process.stdout:
        r += line
        print(line.decode('utf-8'))
    process.wait()
    timeDelta = time.time() - timeStarted
    # Get execution time.
    print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
    out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
    if process.returncode != 0 :
        message='Error exporting '+str(os.path.basename(ifgdim))+'\n' 
        err_file.write(message)
    else:
        message='Stamps export of '+str(os.path.basename(ifgdim))+' successfully completed.\n'
        if k>1 and SMARTHDD =="Y":
            for p in range(0,len(ifgdims)):
                os.remove(ifgdims[p])
                os.remove(dimfiles[p])
                print('removing :'+ifgdims[p][:-3]+'data')
                shutil.rmtree(ifgdims[p][:-3]+'data')
                shutil.rmtree(dimfiles[p][:-3]+'data')
                current_dir=os.getcwd()
                targetdim=glob.glob(current_dir+'/target.dim')
                if len(targetdim)>0:
                    os.remove(targetdim[0])
                    targetdata = os.path.join(current_dir, 'target.data')
                    if len(targetdata)>0 and os.path.isdir(targetdata):
                        shutil.rmtree(targetdata)
    print( message)
    out_file.write(message)
    print( bar_message)
    out_file.write(bar_message)
out_file.close()
err_file.close()

# Check and remove of extra files target.dim and target.data generated by SNAP (SNAP's bug)
current_dir=os.getcwd()
targetdim=glob.glob(current_dir+'/target.dim')
if len(targetdim)>0:
    os.remove(targetdim[0])

targetdata = os.path.join(current_dir, 'target.data')
if os.path.exists(targetdata) and os.path.isdir(targetdata):
    shutil.rmtree(targetdata)
