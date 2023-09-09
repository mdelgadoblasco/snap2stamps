import os
import sys
import glob
import configparser
import argparse
import warnings
import shutil

warnings.filterwarnings('ignore')


parser = argparse.ArgumentParser(description='This script sorts the secondary Sentinel-1 images into folders')
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

#print(config.sections())
#project=config['PROJECT_DEFINITION']
#for key in project:  
#    print(key)

PROJECTFOLDER=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')

#printing variables
print(PROJECTFOLDER)


directory=os.path.join(PROJECTFOLDER,'secondaries')

safeFiles=len(sorted(glob.glob(directory+'/*SAFE/manifest.safe')))
print('Found '+str(safeFiles)+' Sentinel-1 uncompressed files')
for filename in sorted(glob.glob(directory+'/*SAFE/manifest.safe')):
    if filename.startswith('S1'):
        name=os.path.join(directory,filename)
        print(name)
        head, tail = os.path.split(name)
        subdirectory=os.path.join(directory,tail[17:25])
        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)
        source=name
        destination=os.path.join(subdirectory,tail)
        print('Moving '+source+' to '+destination)
        shutil.move(source,destination)
    else:
        continue

safeFiles=len(sorted(glob.glob(directory+'/*zip')))
print('Found '+str(safeFiles)+' Sentinel-1 compressed files')
for filename in sorted(glob.glob(directory+'/*.zip')):
    print(filename)
    if os.path.basename(filename).startswith('S1'):
        print(os.path.basename(filename))
        subdirectory=os.path.join(directory,os.path.basename(filename)[17:25])
        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)
        destination=os.path.join(subdirectory,os.path.basename(filename))
        print('Moving '+filename+' to '+destination)
        shutil.move(filename,destination)
    else:
        continue


