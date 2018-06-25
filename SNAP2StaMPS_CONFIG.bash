# Similar to SNAP2StaMPS_CONFIG.sh which include the shell script to call the other InSAR processing softwares.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Author: Jose Manuel Delgado Blasco
# Organization: Research Group Microgeodesia di Jaen, University of Jaen
# 
# THESE SCRIPTS ARE PROVIDED TO YOU "AS IS" WITH NO WARRANTIES OF CORRECTNESS. USE AT YOUR OWN RISK.
#
# These are shell scripts that call routines of the ESA SentiNel Application Platform (SNAP) software (version 6.0 or higher).
# These scripts are not a distribution of the ESA SNAP software itself.
# These scripts are open-source contributions and should not be mistaken for official Applications within SNAP.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# modifications

export SNAP2STAMPS="/home/mdelgado/software/git_snap2stamps"


## --------------------------------------------------- ##
export PATH=${PATH}:$STAMPS_ISCE/bin