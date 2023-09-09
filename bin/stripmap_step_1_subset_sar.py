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

inputfile = sys.argv[1]

warnings.filterwarnings('ignore')
sys.stdout.flush()

parser = argparse.ArgumentParser(description='This script runs the spatial subset using defined AOI')
parser.add_argument("--ProjFile","-F", type=str)

args = parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile = args.ProjFile
    inputfile=configfile

bar_message='\n#####################################################################\n'
# Setting LD_LIBRARY_PATH for SNAP
#os.environ["LD_LIBRARY_PATH"] = os.getcwd()
os.environ["LD_LIBRARY_PATH"] ="."
# Getting configuration variables from inputfile
config = configparser.ConfigParser()
config.read(configfile)

PROJECT=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
GRAPH=config['PROJECT_DEFINITION'].get('GRAPHSFOLDER')

OVERWRITE=config['PROC_OPTIONS'].get('OVERWRITE')
SMARTHDD=config['PROC_OPTIONS'].get('SMARTHDD')

POLARISATION=config['PROC_PARAMETERS'].get('POLARISATION')
MASTERFOLDER=config['PROC_PARAMETERS'].get('MASTER')
masterfolder=MASTERFOLDER
CACHE=config['COMPUTING_RESOURCES'].get('CACHE')
CPU=config['COMPUTING_RESOURCES'].get('CPU')
######################################################################################
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
#    from shapely import wkt
#    polygon = wkt.dumps(gdf['geometry'][0])
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


#############################################################################
### TOPSAR Splitting (Assembling) and Apply Orbit section ####
############################################################################
# Checking GPT
if not os.path.exists(GPT):
    errormessage="GPT executable not found in "+GPT+".Processing aborted"
    print(errormessage)
    sys.exit(errormessage)


######################################################################################
################################### TSX Subsetting ###################################
##### Dont forget to move your master subset into a newly created master folder! #####
# Folders involved in this processing step
secondariesplittedfolder=PROJECT+'/secondaries'
outputsubsetfolder=PROJECT+'/subset'
logfolder=PROJECT+'/logs'

if not os.path.exists(outputsubsetfolder):
                os.makedirs(outputsubsetfolder)
if not os.path.exists(logfolder):
                os.makedirs(logfolder)

outlog=logfolder+'/subset_stdout.log'

# Original Snap graph and replaced Snap graph for subsettting
graphxml=GRAPH+'/stripmap_TSX_Subset.xml'
print(graphxml)
graph2run=GRAPH+'/subset_2run.xml'

out_file = open(outlog, 'a')
err_file=out_file

# Processing layout
print(bar_message)
out_file.write(bar_message)
message='## Subsetting started:\n'
print(message)
out_file.write(message)
print(bar_message) 
out_file.write(bar_message)
k=0
timeStarted_global = time.time()
# Iterate trough all files in the secondariesfolder
for xmlfile in glob.iglob(secondariesplittedfolder + '/*/*/*.xml'):
    print(xmlfile)
    k=k+1
    # Create name of the output subset file
    head, tail = os.path.split(os.path.join(secondariesplittedfolder, xmlfile))
    message='['+str(k)+'] Processing subset file: '+tail+'\n'
    print(message)
    out_file.write(message)
    outputname=tail[28:36]+'_sub.dim'
    with open(graphxml, 'r') as file :
       filedata = file.read()
    # Replace the target string and generate a new file with replaced names for use in SNAP
    filedata = filedata.replace('INPUTXML',xmlfile)
    filedata = filedata.replace('OUTPUTSUBSETFOLDER',outputsubsetfolder)
    filedata = filedata.replace('OUTPUTFILE',outputname)
    filedata = filedata.replace('POLYGON',polygon)
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
        message='Error computing with subset of splitted secondaries '+str(xmlfile)
        err_file.write(message+'\n')
    else:
        message='Subsetting for data '+str(outputname)+' successfully completed.\n'
        print(message)
        out_file.write(message)
    print(bar_message)
    out_file.write(bar_message)
timeDelta_global = time.time() - timeStarted_global
print('Finished subsetting in ' + str(timeDelta_global) + ' seconds.\n')
out_file.close()

