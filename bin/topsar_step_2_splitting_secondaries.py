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
from subprocess import PIPE, Popen,STDOUT
import shlex
import time

import geopandas as gpd

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
os.environ["LD_LIBRARY_PATH"] ="."
# Getting configuration variables from inputfile
config = configparser.ConfigParser()
config.read(configfile)

PROJECT=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
GRAPH=config['PROJECT_DEFINITION'].get('GRAPHSFOLDER')

OVERWRITE=config['PROC_OPTIONS'].get('OVERWRITE')
SMARTHDD=config['PROC_OPTIONS'].get('SMARTHDD')

POLARISATION=config['PROC_PARAMETERS'].get('POLARISATION')
MASTERFOLDER=config['PROC_PARAMETERS'].get('MASTERFOLDER')

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
    #polygon = wkt.dumps(gdf['geometry'][0])
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
if not os.path.exists(str(GPT)):
	errormessage="GPT executable not found in "+GPT+".Processing aborted"
	print(errormessage)
	sys.exit(errormessage)
# Initializing set-up
secondariesfolder=os.path.join(PROJECT,'secondaries')
masterfolder=os.path.join(PROJECT,'MasterSplit')
splitfolder=os.path.join(PROJECT,'split')
logfolder=os.path.join(PROJECT,'logs')
graphfolder=os.path.join(PROJECT,'graphs')

if not os.path.exists(splitfolder):
	os.makedirs(splitfolder)
if not os.path.exists(logfolder):
	os.makedirs(logfolder)
if not os.path.exists(graphfolder):
	os.makedirs(graphfolder)
########################################
# Define execute command
def execute(command):
	process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

	# Poll process for new output until finished
	while True:
		nextline = process.stdout.readline()
		if nextline == '' :#and process.poll() is not None:
			break
		sys.stdout.write(nextline.decode('utf-8'))
		sys.stdout.flush()

	output = process.communicate()[0]
	exitCode = process.returncode

#	if (exitCode == 0):
#		return output
#	else:
#		raise ProcessException(command, exitCode, output)
########################################
graph2run=os.path.join(graphfolder,'splitgraph2run.xml')
outlog=os.path.join(logfolder,'splitsecondaries.log')
out_file = open(outlog, 'a')
err_file=out_file

print( bar_message)
out_file.write(bar_message)
message='## TOPSAR Splitting and Apply Orbit\n'
print( message)
out_file.write(message)
print( bar_message)
out_file.write(bar_message)
k=0
for acdatefolder in sorted(os.listdir(secondariesfolder)):
	k=k+1
	print( '['+str(k)+'] Folder: '+acdatefolder)
	out_file.write('['+str(k)+'] Folder: '+acdatefolder+'\n')
	print( os.path.join(secondariesfolder, acdatefolder))
	out_file.write(str(os.path.join(secondariesfolder, acdatefolder))+'\n')
#	files = glob.glob(os.path.join(secondariesfolder, acdatefolder) + '/*.safe')
	files = glob.glob(os.path.join(secondariesfolder, acdatefolder) + '/*.zip')
	if len(files)==0:
		files = glob.glob(os.path.join(secondariesfolder, acdatefolder) + '/*SAFE/manifest.safe')
	print( files)
	out_file.write(str(files)+'\n')
	head, tail = os.path.split(os.path.join(str(files)))
	#splitsecondariesfolder=splitfolder+'/'+tail[17:25]
	#splitsecondariesfolder=splitfolder+'/'+acdatefolder[0:8]
	splitsecondariesfolder=splitfolder
	if not os.path.exists(splitsecondariesfolder):
		os.makedirs(splitsecondariesfolder)
	for masters in sorted(glob.glob(masterfolder+'/*dim')):
		IW=masters[-7:-4]
		print(IW)
		outputname=tail[17:25]+'_'+IW+'.dim'
		outputname=acdatefolder+'_'+IW+'.dim'
		print('Outname:'+outputname)
		if not os.path.exists(str(splitsecondariesfolder+'/'+outputname)) and OVERWRITE=='N':
			if len(files) == 1 :
				graphxml=os.path.join(GRAPH,'topsar_secondaries_split_applyorbit.xml')
			# Read in the file
				print( 'FILE(s) : '+files[0])
				with open(graphxml, 'r') as file :
					filedata = file.read()
				# Replace the target string
				filedata = filedata.replace('INPUTFILE', files[0])
				filedata = filedata.replace('IWs',IW)
				filedata = filedata.replace('POLARISATION',POLARISATION)
				filedata = filedata.replace('POLYGON',polygon)
				filedata = filedata.replace('OUTPUTFILE',splitsecondariesfolder+'/'+outputname)
				# # Write the file out again
				with open(graph2run, 'w') as file:
					file.write(filedata)
			if len(files) > 1 :
				graphxml=os.path.join(GRAPH,'topsar_secondaries_assemble_split_applyorbit.xml')
				with open(graphxml, 'r') as file :
					filedata = file.read()
				# Replace the target string
				filedata = filedata.replace('INPUTFILE1', files[0])
				filedata = filedata.replace('INPUTFILE2', files[1])
				filedata = filedata.replace('IWs',IW)
				filedata = filedata.replace('POLARISATION',POLARISATION)
				filedata = filedata.replace('POLYGON',polygon)
				filedata = filedata.replace('OUTPUTFILE',splitsecondariesfolder+'/'+outputname)
				# Write the file out again
				with open(graph2run, 'w') as file:
					file.write(filedata)
	
			args = [ GPT, graph2run, '-c', CACHE, '-q', CPU]
#			args = GPT+' '+graph2run+' -c '+CACHE+' -q '+CPU
			print( args)
			out_file.write(str(args)+'\n')
			# launching the process
			###process = subprocess.Popen(args, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			timeStarted = time.time()
			process = Popen(args,  bufsize=1, stdout=PIPE, stderr=STDOUT)
			r = b""
			for line in process.stdout:
				r += line
				print(line.decode('utf-8'))
			process.wait()
##			execute(args)
			###stdout = process.communicate()[0]
			###print ('SNAP STDOUT:{}'.format(stdout))
			timeDelta = time.time() - timeStarted                     # Get execution time.
			print(('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.'))
			out_file.write('['+str(k)+'] Finished process in '+str(timeDelta)+' seconds.\n')
			if process.returncode != 0 :
				message='Error splitting secondaries '+str(files)
				err_file.write(message)
			else: 
				message='Split secondaries '+str(files)+' successfully completed.\n'
				print( message)
				out_file.write(message)
			print( bar_message)
		else:
			message="File :"+outputname+" already exists. Processing skipped"
			print(message)
			print(bar_message)
			out_file.write(message)
			out_file.write(bar_message)
out_file.write(bar_message)
out_file.close()
