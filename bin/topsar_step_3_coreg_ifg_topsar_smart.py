### Python script to use SNAP as InSAR processor compatible with StaMPS PSI processing
# Author Jose Manuel Delgado Blasco
# Date: 21/06/2018
# Updated: 01/06/2023
# Version: 2.0

# Step 0 : preparing secondary images in folder structure
# Step 1 : Master TOPSAR Splitting (Assembling) and Apply Orbit
# Step 2 : TOPSAR Splitting (Assembling) and Apply Orbit of Secondary Images
# Step 3 : Coregistration and Interferogram generation
# Step 4 : StaMPS export
# Step 5 : Plotting secondaries and interferometric phase

# Added option for CACHE and CPU specification by user
# Planned support for DEM selection and ORBIT type selection 
import configparser
import argparse
import warnings
import io
import os
from pathlib import Path
import sys
import glob
from subprocess import PIPE, Popen
import shlex
import time

import geopandas as gpd

sys.stdout.flush()
inputfile = sys.argv[1]
warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='This script executes the coregistration and ifg computation of Sentinel-1 image pairs')
parser.add_argument("--ProjFile","-F", type=str)

args = parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile = args.ProjFile

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

MASTERFOLDER=config['PROC_PARAMETERS'].get('MASTERFOLDER')
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

print(polygon)

###################################################################
## GETTING PATH to gpt executable 
SNAPFOLDER=config['SNAP_GPT'].get('SNAP_INSTALLATION_FOLDER')
GPT=os.path.join(SNAPFOLDER,'bin','gpt')
if os.name == 'nt':
    GPT=os.path.join(SNAPFOLDER,'bin','gpt.exe')

######################################################################################
## TOPSAR Coregistration and Interferogram formation ##
######################################################################################
# Checking GPT
if not os.path.exists(GPT):
        errormessage="GPT executable not found in "+GPT+".Processing aborted"
        print(errormessage)
#        sys.exit(errormessage)
# Initializing set-up
masterfolder=os.path.join(PROJECT,'MasterSplit')
secondariesplittedfolder=os.path.join(PROJECT,'split')
outputcoregfolder=os.path.join(PROJECT,'coreg')
outputifgfolder=os.path.join(PROJECT,'ifg')
graphfolder=os.path.join(PROJECT,'graphs')
logfolder=os.path.join(PROJECT,'logs')

if not os.path.exists(outputcoregfolder):
	os.makedirs(outputcoregfolder)
if not os.path.exists(outputifgfolder):
	os.makedirs(outputifgfolder)
if not os.path.exists(graphfolder):
	os.makedirs(graphfolder)
if not os.path.exists(logfolder):
	os.makedirs(logfolder)

outlog=os.path.join(logfolder,'coreg_ifg_proc_stdout.log')
graph2run=os.path.join(graphfolder,'coreg_ifg2run.xml')

out_file = open(outlog, 'a')
err_file=out_file

def get_nbursts(inputfile):
    print('Checking N bursts in file '+inputfile)
    file1=open(inputfile,'r')
    Lines=file1.readlines()

    count=0
    for line in Lines:
        count +=1
        if "burstList" in line:
            print("Line {} :{}".format(count,line.strip()))
            nbursts=Lines[count].split('>')[1].split('<')[0]
            print(nbursts)
            return int(nbursts)
    return 1


print (bar_message)
out_file.write(bar_message)
message='## Coregistration and Interferogram computation started:\n'
print( message)
out_file.write(message)
print (bar_message) 
out_file.write(bar_message)

for masters in sorted(glob.glob(masterfolder+'/*dim')):
    k=0
    nmasters=len(sorted(glob.glob(masterfolder+'/*dim')))
    print('N masters:'+str(nmasters))
    graphxml=os.path.join(GRAPH,'topsar_coreg_ifg_computation')
    if nmasters==1:
        graphxml=graphxml+'_subset'

    if get_nbursts(os.path.join(masterfolder,masters)) ==1:
        graphxml=graphxml+'_noESD'

    if extDEM=="":
        graphxml=graphxml+'.xml'
    else:
        graphxml=graphxml+'_extDEM.xml'

    print('graph :'+graphxml)
    IW=masters[-7:-4]
    print(masters)
    print(IW)
    for dimfile in sorted(glob.iglob(secondariesplittedfolder + '/*'+IW+'.dim')):
        print (dimfile)
        k=k+1
        head, tail = os.path.split(os.path.join(secondariesplittedfolder, dimfile))
        message='['+str(k)+'] Processing secondaries file :'+tail+'\n'
        print( message)
        out_file.write(message)
        head , tailm = os.path.split(os.path.join(masters))
        outputname=tailm[17:25]+'_'+tail[0:8]+'_'+IW
        outputname=tailm[0:8]+'_'+tail[0:8]+'_'+IW
        print(outputname)
        with open(graphxml, 'r') as file :
            filedata = file.read()
        # Replace the target string
        filedata = filedata.replace('MASTER',masters)
        filedata = filedata.replace('SECONDARY', dimfile)
        filedata = filedata.replace('EXTERNALDEM',extDEM)
        filedata = filedata.replace('OUTPUTCOREGFOLDER',outputcoregfolder)
        filedata = filedata.replace('OUTPUTIFGFOLDER', outputifgfolder)
        filedata = filedata.replace('OUTPUTFILE',outputname)
        filedata = filedata.replace('POLYGON',polygon)
        # Write the file out again
        with open(graph2run, 'w') as file:
            file.write(filedata)
        args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
            # Check if exists
        if not os.path.exists(str(outputcoregfolder+'/'+outputname+'.dim')) and OVERWRITE=='N':
            # Launch the processing		
            timeStarted = time.time()
            process = Popen(args,  bufsize=1, stdout=PIPE, stderr=PIPE)
            r = b""
            for line in process.stdout:
                r += line
                print(line.decode('utf-8'))
            process.wait()
            timeDelta = time.time() - timeStarted   # Get execution time.
            print('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.')
            out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
            if process.returncode != 0 :
                print('Returncode :'+str(process.returncode))
                message='Error computing with coregistration and interferogram generation of splitted secondaries '+str(dimfile)
                err_file.write(message+'\n')
            else:
                message='Coregistration and Interferogram computation for data '+str(tail)+' successfully completed.\n'
            print (message)
            out_file.write(message)
            #print (bar_message)
            ## Cleaning up duplicated bands and info
            if SMARTHDD == 'Y' :
                print('Optimising disk data volume option activated!')
                srccoreg=sorted(glob.glob(outputcoregfolder+'/*.data/'))[0]
                ifile=glob.glob(srccoreg+'/i*mst*img')[0]
                qfile=glob.glob(srccoreg+'/q*mst*img')[0]
                srcifg=sorted(glob.glob(outputifgfolder+'/*.data'))[0]
                dem1=glob.glob(srcifg+'/elevation.img')#[0]
                if len(dem1)>0:
                    dem=dem1[0]
                lat1=glob.glob(srcifg+'/orthorectifiedLat.img')#[0]
                if len(lat1)>0:
                    lat=lat1[0]
                lon1=glob.glob(srcifg+'/orthorectifiedLon.img')#[0]
                if len(lon1)>0:
                    lon=lon1[0]
            #else:
            #	print('Optimising disk data volume option deactivated!')
            if SMARTHDD == 'Y' and k>1:
                #print('Removing duplicated files:')
                # Removing master coregistered from stacks (from second onwards)
                files = glob.glob(outputcoregfolder+'/'+outputname+'.data/*mst*.img')
                if len(files)>0:
                    os.remove(files[0])
                #	print(files[0])
                #	print('linking :'+ifile+' '+files[0])
                    os.symlink(ifile,files[0])
                if len(files)==2:
                    os.remove(files[1])
                #	print(files[1])
                #	print('linking :'+qfile+' '+files[1])
                    os.symlink(qfile,files[1])
                # Removing orthorectified Lat/Long bands (all equal for each stack)
                files = glob.glob(outputifgfolder+'/'+outputname+'.data/orthorectified*.img')
                if len(files)>0:
                    os.remove(files[0])
                #	print(files[0])
                #	print('linking :'+lat+' '+files[0])
                    os.symlink(lat,files[0])
                if len(files)==2:
                    os.remove(files[1])
                #	print(files[1])
                #	print('linking :'+lon+' '+files[1])
                    os.symlink(lon,files[1])
                # Removing elevation band (all equal for each stack)
                files = glob.glob(outputifgfolder+'/'+outputname+'.data/elevation.img')
                if len(files)>0:
                    os.remove(files[0])
                #	print(files[0])
                #	print('linking :'+dem+' '+files[0])
                    os.symlink(dem,files[0])
            print(bar_message)
        else:
            message="File :"+outputname+" already exists. Processing skipped"
            print(message)
            print(bar_message)
            out_file.write(message)
        out_file.write(bar_message)
out_file.close()
