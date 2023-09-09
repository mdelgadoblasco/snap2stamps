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
    sys.exit()

SNAPHIDDEN=config['SNAP_GPT'].get('SNAP_HOME_DIR')
PALETTES=os.path.join(SNAPHIDDEN,'auxdata','color_palettes')

##################################################################################
# Checking GPT
if not os.path.exists(GPT) or not os.path.exists(PCONVERT):
    errormessage="GPT or PCONVERT executable not found in "+os.path.dirname(GPT)+".Processing aborted"
    print(errormessage)
    sys.exit(errormessage)

######################################################################################
## Plotting Slaves amplitude and Interferometric phase ##
######################################################################################
# Initializing set-up
masterfolder=PROJECT+'/MasterSplit'
secondariesplittedfolder=PROJECT+'/split'
coregfolder=PROJECT+'/coreg'
ifgfolder=PROJECT+'/ifg'
graphfolder=PROJECT+'/graphs'
logfolder=PROJECT+'/logs'
plotfolder=PROJECT+'/plot/'+mode
if not os.path.exists(graphfolder):
        os.makedirs(graphfolder)
if not os.path.exists(logfolder):
        os.makedirs(logfolder)
if not os.path.exists(plotfolder):
	os.makedirs(plotfolder)

outlog=logfolder+'/plot_stdout.log'
if mode == 'split':
	graphxml=GRAPH+'/topsar_plot_amplitude_deburst.xml'
	searchfolder=secondariesplittedfolder
	ibandname='i_*'+POLARISATION
	qbandname='q_*'+POLARISATION
elif mode == 'coreg':
	graphxml=GRAPH+'/plot_amplitude.xml'
	searchfolder=coregfolder
	ibandname='i_*'+POLARISATION+'_slv1'
	qbandname='q_*'+POLARISATION+'_slv1'
elif mode == 'ifg':
	graphxml=GRAPH+'/plot_phase.xml'
	searchfolder=ifgfolder
	ibandname='i_ifg_*'+POLARISATION
	qbandname='q_ifg_*'+POLARISATION
graph2run=graphfolder+'/plot2run_'+mode+'.xml'

out_file = open(outlog, 'a')
err_file=out_file

print (bar_message)
out_file.write(bar_message)
message='## Plotting secondaries amplitude and Interferometric phase started:\n'
print( message)
out_file.write(message)
print (bar_message)
out_file.write(bar_message)


for masters in sorted(glob.glob(masterfolder+'/*dim')):

	IW=masters[-7:-4]
	print(IW)
	k=0
	for dimfile in sorted(glob.iglob(searchfolder + '/*'+IW+'.dim')):
		print (dimfile)
		k=k+1
		head, tail = os.path.split(os.path.join(searchfolder, dimfile))
		message='['+str(k)+'] Processing file :'+tail+'\n'
		print( message)
		out_file.write(message)
		tailm=os.path.basename(masters)
		#outputname=tailm[17:25]+'_'+tail[0:8]+'_'+IW
		#outputname=outputname+'_'+mode
		outputname=tail[:-4]+'_'+mode
		print(outputname)
		#outputname2=outputname+'_coreg'
		#outputname3=outputname+'_phase'
		print(searchfolder+'/'+tail[:-3]+'data/'+ibandname+'*img')
		iband=glob.glob(searchfolder+'/'+tail[:-3]+'data/'+ibandname+'*.img')
		iband=os.path.basename(iband[0])
		iband=iband.split('.')[0]
		qband=glob.glob(searchfolder+'/'+tail[:-3]+'data/'+qbandname+'*.img')
		qband=os.path.basename(qband[0])
		qband=qband.split('.')[0]
		print(iband)
		print(qband)
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
			color=PALETTES+'/spectrum_cycle.cpd'
			#color=PALETTES+'/spectrum_large.cpd'
			#color=PALETTES+'/JET.cpd'
			inputfile=plotfolder+'/'+outputname+'.dim'
			# For amplitude info
			if mode == 'ifg':
				args=[PCONVERT,'-b','1','-c',color,'-f','png','-o',plotfolder,inputfile]
			else :
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
