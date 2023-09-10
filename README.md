# SNAP2StaMPS v2    <a href="https://doi.org/10.5281/zenodo.8331352"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.8331352.svg" alt="DOI"></a> [![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/) [![Github All Releases](https://img.shields.io/github/downloads/mdelgadoblasco/snap2stamps/total.svg)](https://GitHub.com/mdelgadoblasco/snap2stamps/releases/)
SNAP2StaMPS v2: Using SNAP as InSAR processor for StaMPS



This repository and the included scripts call routines of the ESA SentiNel Application Platform (SNAP) to perform TOPSAR interferometric processing producing compatible inputs for the open-source StaMPS package.

***The provided scripts with this SNAP to StaMPS package are not part of the SNAP software. The provided scripts are open-source contributions and should not be mistaken for official Applications within SNAP. The scripts are provided to you "as is" with no warranties of corrections.***

This new provided package (SNAP2StaMPSv2) evolves from the initial SNAP2StaMPS package and will be presented at FRINGE WORKSHOP 2023 in Leeds, September 2023 with zendo doi [10.5281/zenodo.8331352](https://doi.org/10.5281/zenodo.8331352).

Authors: 
- José Manuel Delgado Blasco, "Microgeodesia Jaén" Research Group (MJaén), Jaén, Spain
- Jonas Ziemer, Department for Earth Observation, Friedrich Schiller University Jena (FSU), Germany
- Michael Foumelis, Aristotle University of Thessaloniki (AUTh), Greece
- Clémence Dubois, Department for Earth Observation, Friedrich Schiller University Jena (FSU), Germany

## Description
SNAP2StaMPS version 2 tries to collect feedback and it has been built to minimize issues from the user side due to package installation, or other dependencies due to software versioning, etc. Further, the new version supports the preprocessing of high-resolution TerraSAR-/TanDEM-X Stripmap data including and enhancing the TSX2Stamps package for the preparation of StaMPS PSI processing. TSX2Stamps uses a similar workflow applied to Sentinel-1 TOPSAR data in the previous version of SNAP2StaMPS. The TSX2Stamps package is also freely available for download on GitHub (https://github.com/jziemer1996/TSX2StaMPS). Please find below the general workflow of SNAP2StaMPS v2. For further information, please check the information given below or have a look at the tutorial provided within this repository.

![SNAP2StaMPS_v2_workflow](https://github.com/mdelgadoblasco/snap2stamps_v2/assets/20595425/6ab8fa42-7941-4b85-a8c6-d2e73df37aae)

## Important notes:
### SNAP2StaMPS execution
This new version provides 2 different ways of using the package:
1. Standard Python execution from the command line (similar to version 1)
2. Advanced execution using dockerised software (under testing)

### Before starting:
The scripts are hardcoded to use SRTM 1Sec HGT DEM which are automatically downloaded from the ESA STEP repository. 
> **Note**:
> Coregistration with DEM (Backgeocoding or DEM-Assisted-Coreg) or TopoPhaseRemoval might hang up if the SAR data footprint falls in areas where no valid SRTM1 tile exists. This might happen in areas near the Coastline. To avoid possible issues try to ensure SAR data footprints fall inside valid SRTM1 Sec tiles.

> **Note**:
> Please note that the TSX2Stamps package was developed using an External DEM with a high spatial resolution (5m). For the processing of TSX stripmap data, we highly recommend using an External DEM with a higher spatial resolution than provided by SRTM to ensure the best possible quality for the ingestion in StaMPS. 

> **Warning**:
> If the user wants to use its own External DEM, please ensure it is in geotiff format with no data values as 0.0 and preprocessed using egm84 ellipsoid. Otherwise, ensure to adapt the parameters in the xml graphs accordingly. 

### New project configuration files (for Topsar and Stripmap processing)
Due to the integration of Stripmap data, the new SNAP2StaMPS package consists of two separate branches (SNAP2StaMPSv1 and TSX2Stamps) with two different config files (project_topsar.conf and project_stripmap.conf). Please spend some time understanding the (new) options available in the configuration files.

The new project configuration files include TAGS for newer options such as:
- Sentinel-1 data download from Alaska Satellite Facilities* using the asf_search package
- Support new AOI definition methods, BBOX, WKT, SHP, KML or GeoJSON
- Sentinel-1 master selection methods: AUTO / MANUAL / FIRST / LAST
- and more ...

Since TSX/TDX data is not freely available, the download and auto-master selection is only available for Sentinel-1 data. Consequently, the configuration file of stripmap data comes without these parameters and is slightly different.

>**Note**:
>The Sentinel-1 data download requires the provisioning of valid and registered credentials from ASF in the configuration file section **[SEARCH_PARAMS]** in **ASF_USER** and **ASF_PASS**. If needed, click [here](https://asf.alaska.edu/) to register at the Alaska Satellite Facilities website

See below the detailed information that can be defined within the project_topsar.conf file:

```bash
################### TOPSAR CONFIGURATION FILE #############################
###########################################################################
[PROJECT_DEFINITION] 
PROJECTFOLDER = /media/Storage/SNAP2stamps_test_small/ 
GRAPHSFOLDER = /home/jmdb/SNAPping/SNAP2stamps_v2/tmp/SNAP2stamps/graphs
###########################################################################
[PROC_OPTIONS] 
# Y / N OPTIONS 
OVERWRITE = N
SMARTHDD = Y
PLOTTING = Y
###########################################################################
[PROC_PARAMETERS]
# SENSOR : S1 
SENSOR = S1
POLARISATION = VV
MASTER = /media/Storage/SNAP2stamps_test_small/Master/
# MASTER SELECTION : AUTO / FIRST / LAST / MANUAL 
MASTERSEL = MANUAL
EXTDEM =
###########################################################################
[AOI_DEFINITION]
#AOI_MODE OPTIONS BBOX / SHP / KML / GeoJSON
AOI_MODE = SHP
LONMIN = 54.2
LATMIN = 24.36
LONMAX = 55.66
LATMAX = 25.42
AOI_FILE = /media/Storage/SNAP2stamps_test/aoi/aoi.shp
############################################################################
[SEARCH_PARAMS]
# autoDownload : Y / N 
autoDownload = N
TRACK = 117
# beamMode : SLC / GRD
beamMode = SLC       
# START/ STOP in YYYY-MM-DD
START = 2020-02-01
END = 2020-04-16
# SAT : S1 / S1A / S1B
SAT= S1A
ASF_USER = 
ASF_PASS = 
# Number of Parallel Downloads (NPD)
[SEARCH_PDOWNLOADS]
NPD = 4
############################################################################
[SNAP_GPT]
SNAP_INSTALLATION_FOLDER = /home/jmdb/anaconda/envs/SNAP2stamps/SNAP/
SNAP_HOME_DIR = /home/jmdb/anaconda/envs/SNAP2stamps/.SNAP  
############################################################################
[COMPUTING_RESOURCES]
CPU = 8
CACHE = 16G
############################################################################
```
# Using the SNAP2StaMPS package
## 1. Standard Execution: Python package
### 1.1. Dependencies / Requirements
1. Git
2. conda: SNAP2StaMPS v2 includes the definition of a yml file which includes a customized ESA SNAP (v.9.0) conda package.
3. SNAP 9.0 dependencies to be installed in OS libfftw3, libgfortran (example for Linux OS). 
>**Note**: Using the environment yml provided there is no need for additional installation of ESA SNAP

### 1.2. Installation
```bash
sudo apt update
sudo apt install git libfftw3 libgfortran
git clone https://github.com/mdelgadoblasco/snap2stamps.git 
conda env create -f snap2stamps_environment.yml
```

### 1.3. Usage

The user may choose to run:
1. The auto_run.py script that automates the full workflow with the command below.
```bash
python auto_run.py -F project_topsar.conf # for Sentinel-1 TOPSAR data
python auto_run.py -F project_stripmap.conf # for TSX Stripmap data
```
By running the above script the workflow may include the Sentinel-1 data download and the master selection according to the definition of the project_topsar.conf file. For TSX, these options are not available and the data download has to be done manually.

2. The step-by-step approach for 
  - Sentinel-1 TOPSAR processing:
```bash
python asf_s1_downloader.py -F project.conf                       #[optional]
python topsar_step_0_secondaries_prep.py -F project.conf
python automaster.py -F project.conf                              #[optional]
python topsar_step_1_splitting_master_multi_IW.py -F project.conf
python topsar_step_2_splitting_secondaries.py -F project.conf
python topsar_step_3_coreg_ifg_topsar_smart.py -F project.conf
python topsar_step_4_plotting_all.py -F project.conf              #[optional]
python topsar_step_5_stamps_export_multiIW.py -F project.conf
```
  - TerraSAR-X Stripmap processing:
```bash
python stripmap_tsx_step_0a_unpack_sar_scenes.py -F project.conf
python stripmap_tsx_step_0b_secondaries_prep.py -F project.conf
python stripmap_tsx_step_1_subset_sar.py -F project.conf
python stripmap_step_1b_masterselection.py -F project.conf
python stripmap_tsx_step_2_coreg_sar.py -F project.conf
python stripmap_tsx_step_3_ifg_sar.py -F project.conf
python stripmap_tsx_step_4_plotting_all.py -F project.conf        #[optional]
python stripmap_tsx_step_5_stamps_export.py -F project.conf
```
A new feature of this release is the plotting of the images resulting from subsetting, coregistration, and interferogram generation. To generate the plots run the following code by specifying the desired mode:
- for splitted or subsetted files:
```bash
  python auto_run.py -F project_topsar.conf -M split
```
- for coregistered files:
```bash
  python auto_run.py -F project_topsar.conf -M coreg
```
- for the interferograms:
```bash
  python auto_run.py -F project_topsar.conf -M ifg
```
The same applies to stripmap data by using the project_stripmap.conf file instead of topsar.

# v2.0 Release features
- SNAP2StaMPS update to **Python 3.11 and SNAP v9.0**
- Autorun script to **automate full processing** steps
- Sentinel-1 **master selection** script for automation
- Master splitting in the command line
- Support to Sentinel-1 Multi Subswath
- Support to single burst AOI
- Support to TerraSAR-X Stripmap with DEM assisted coregistration
- Support to BBOX, WKT, SHP, KML, GeoJSON formats for AOI definition
- Support to External DEM usage (DEM preparation routines not included)
- Plotting coregistered slcs and ifgs 
- Smart options for disk optimization
  
# Contributing
- José Manuel Delgado Blasco (Research Group Microgeodesia Jaén, Jaén, Spain)
- Jonas Ziemer (University of Jena, Germany)
- Michael Foumelis (University of Thessaloniki, Greece)
- Clémence Dubois (University of Jena, Germany)

The team is open to new contributions, so don't be shy and share them with the community.

# Acknowledgments
We want to acknowledge:
- Fabio Cian
- Andreas Braun
- Andre Theron
## Questions and inquiries 
For questions and inquiries, we want to promote the usage of the [ESA STEP Forum](https://forum.step.esa.int/) that has been used very much until now.

# License
![image](https://github.com/mdelgadoblasco/snap2stamps_v2/assets/20595425/e36c71bc-8c10-4bd8-ae92-c6b4dac077c7)
**CC BY-NC-SA**: [Creative Commons Attribution-NonCommercial-ShareAlike](https://creativecommons.org/licenses/by-nc-sa/4.0)

This license lets others remix, adapt, and build upon your work non-commercially, as long as they credit you and license their new creations under the identical terms.
