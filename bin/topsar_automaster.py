import os
import sys
import numpy as np
import configparser
import argparse
import warnings

warnings.filterwarnings('ignore')

parser = argparse.ArgumentParser(description='This script selects a Master image if AUTO mode was selected')
parser.add_argument("--ProjFile","-F", type=str)
parser.add_argument("--Mode","-M", type=str)

args = parser.parse_args()

def usage():
    message='####################################################\n'
    message=message+'Usage: python '+sys.argv[0]+' -F [project.conf] -M [mode] \n'
    message=message+'               project.conf file\n'
    message=message+'               mode : AUTO/FIRST/LAST\n'
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


print(configfile)
config = configparser.ConfigParser()
config.read(configfile)

PROJECTFOLDER=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
MASTERFOLDER=config['PROC_PARAMETERS'].get('MASTER')
MODE=config['PROC_PARAMETERS'].get('MASTERSEL')

#printing variables
print(PROJECTFOLDER)
secondaries=os.path.join(PROJECTFOLDER,'secondaries')

## Searching secondaries folders and files downloaded
print(len(next(os.walk(secondaries))[1]))

files = folders = 0
for _, dirnames, filenames in os.walk(secondaries):
  # ^ this idiom means "we won't be using this value"
    files += len(filenames)
    folders += len(dirnames)
print ("{:,} files, {:,} folders".format(files, folders))

dirs=next(os.walk(secondaries))[1]
print(dirs)

options=range(folders+1)
print(options)

import numpy as np
if mode=='AUTO':
    sel=int(np.floor(folders/2)-1)
    print(sel)
elif int(mode) in options:
    sel=int(mode)-1
    print(sel)
elif mode=='FIRST':
    sel=options[0]
elif mode=='LAST':
    sel=options[-1]
elif mode=='MANUAL':
    print("Master selection defined MANUAL. Please proceed accordingly!")
    sys.exit()
else:
    print('No valid option found! Using automaster!')
    sel=int(np.floor(folders/2)-1)
print('Selected Master date: '+dirs[sel])

try:
    if sel is not None:
    ## Moving files to MASTER folder
        source = os.path.join(secondaries,dirs[sel])
        destination = MASTERFOLDER
        print(destination)
    # gather all files
        allfiles = os.listdir(source)
        print(allfiles)

    # iterate on all files to move them to destination folder
        for f in allfiles:
            src_path = os.path.join(source, f)
            dst_path = os.path.join(destination, f)
            os.rename(src_path, dst_path)

    # Remove empty folder from secondaries folder
        os.rmdir(os.path.join(secondaries,dirs[sel]))
except:
    print('Master to be selected and prepared manually by the user')
    pass

