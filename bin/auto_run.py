from subprocess import Popen, PIPE, STDOUT
import os
import sys
import time
import warnings
import argparse
import configparser
import subprocess

warnings.filterwarnings('ignore')
sys.stdout.flush()

parser = argparse.ArgumentParser(description='This script runs automatically all the steps for single master DInSAR processing')
parser.add_argument("--ProjFile","-F", type=str)

args = parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile = args.ProjFile

####################################################
def execute(step,param1,param2):
    if 'step_4' in step or 'automaster' in step:
        args = [ 'python', step, '-F', param1, '-M', param2]
    else:
        args = [ 'python', step, '-F', param1]
    print( args)
    # Launching process
    timeStarted = time.time()
    process = Popen(args,  bufsize=1, stdout=PIPE, stderr=STDOUT)
    r = b""
    for line in process.stdout:
        r += line
        print(line.decode('utf-8'))
    process.wait()
    timeDelta = time.time() - timeStarted
    # Get execution time.
    print(' Finished process in '+str(timeDelta)+' seconds.')
    if process.returncode != 0 :
        message='Error running '+step+'\n'
    else:
        message='Step '+step+' successfully completed.\n' 
    print(message)
    return process.returncode

#config=sys.argv[1]
# Getting configuration variables from inputfile
config = configparser.ConfigParser()
config.read(configfile)
PLOTTING=config['PROC_OPTIONS'].get('PLOTTING')
#DOWNLOAD=config['SEARCH_PARAMS'].get('autoDownload')
SENSOR=config['PROC_PARAMETERS'].get('SENSOR')
#MASTERSEL=config['PROC_PARAMETERS'].get('MASTERSEL')
## Execute the different steps
if SENSOR == 'S1':
    DOWNLOAD=config['SEARCH_PARAMS'].get('autoDownload')
    MASTERSEL=config['PROC_PARAMETERS'].get('MASTERSEL')
    if DOWNLOAD == 'Y':
        execute('asf_s1_downloader.py', configfile,'')

    execute('topsar_step_0_secondaries_prep.py', configfile,'')
    if MASTERSEL!='MANUAL':
        execute('topsar_automaster.py', configfile, MASTERSEL)
    execute('topsar_step_1_splitting_master_multi_IW.py',configfile,'')
    execute('topsar_step_2_splitting_secondaries.py', configfile,'')
    execute('topsar_step_3_coreg_ifg_topsar_smart.py', configfile,'')

    if PLOTTING == 'Y':
        execute('topsar_step_4_plotting_all.py', configfile, 'ifg')
        execute('topsar_step_4_plotting_all.py', configfile,'coreg')

    execute('topsar_step_5_stamps_export_multiIW.py', configfile,'')

elif SENSOR == 'TSX' or SENSOR == 'TDX':
    execute('stripmap_step_0a_unpack_sar_scenes.py', configfile,'')
    execute('stripmap_step_0b_secondaries_prep.py', configfile,'')
    execute('stripmap_step_1_subset_sar.py', configfile,'')
    subprocess.call(['python', 'stripmap_step_1b_masterselection.py'] + list(sys.argv[1:]))
    execute('stripmap_step_2_coreg_sar.py', configfile,'')
    execute('stripmap_step_3_ifg_sar.py', configfile,'')

    if PLOTTING == 'Y':
        execute('stripmap_step_4_plotting_all.py', configfile, 'split')
        execute('stripmap_step_4_plotting_all.py', configfile, 'ifg')
        execute('stripmap_step_4_plotting_all.py', configfile,'coreg')

    execute('stripmap_step_5_stamps_export.py', configfile, '')
else:
    print('Sensor not recognized! Please check project configuration file')
    print('Processing terminated')
    print('In case sensor is not S1, TSX or TDX you may run the scripts under your own responsability as these scripts had not been tested yet with other sensors')
    print('Feedback welcome through the STEP Forum https://step.esa.int')

