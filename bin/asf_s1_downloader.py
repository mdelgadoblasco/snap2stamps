import os
import sys
import configparser
import argparse
import asf_search as asf
import warnings
warnings.filterwarnings('ignore')

parser=argparse.ArgumentParser(description='This script downloads Sentinel-1 data from Alaska Satellite Facilities')
parser.add_argument("--ProjFile","-F",type=str)

args=parser.parse_args()
if not args.ProjFile:
    print("No Input File detected")
    sys.exit(-1)
else:
    configfile=args.ProjFile

print(configfile)
config=configparser.ConfigParser()
config.read(configfile)

PROJECTFOLDER=config['PROJECT_DEFINITION'].get('PROJECTFOLDER')
directory=os.path.join(PROJECTFOLDER,'secondaries')
print(directory)

TRACK=int(config['SEARCH_PARAMS'].get('TRACK'))
beamMode=config['SEARCH_PARAMS'].get('beamMode')
START=config['SEARCH_PARAMS'].get('START')
END=config['SEARCH_PARAMS'].get('END')
SAT=config['SEARCH_PARAMS'].get('SAT')

print(TRACK)
print(beamMode)
print(START)
print(END)

USER=config['SEARCH_PARAMS'].get('ASF_USER')
PASS=config['SEARCH_PARAMS'].get('ASF_PASS')
NPD=int(config['SEARCH_PDOWNLOADS'].get('NPD'))

if not os.path.exists(directory):
    os.makedirs(directory)


if SAT == "S1":
    myplatform=asf.SENTINEL1
elif SAT == "S1A":
    myplatform=asf.SENTINEL1A
elif SAT =="S1B":
    myplatform=asf.SENTINEL1B
print(myplatform)
    
if beamMode=="SLC":
    procType=[asf.PRODUCT_TYPE.SLC]
else:
    procType=[asf.PRODUCT_TYPE.GRD_HD,asf.PRODUCT_TYPE.GRD_HS]
    
print(procType)

###########################################################
## INITITATING SESSION WITH CREDENTIALS
session=asf.ASFSession()
session.auth_with_creds(USER,PASS)

#########################################################
## GETTING AOI DEFINITION
#print('###############################################')
#print('Getting AOI')
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
    import geopandas as gpd
    if aoi_mode != 'KML':
        gdf=gpd.read_file(AOIFile)
    else:
        import fiona
        fiona.drvsupport.supported_drivers['KML'] = 'rw'
        gdf = gpd.read_file(AOIFile, driver='KML')
        #polygon=str(gdf['geometry'].wkt)

    #from shapely import wkt
#    polygon = wkt.dumps(gdf['geometry'][0])
    #polygon=gdf['geometry'].envelop
#    bounds=gdf.bounds
    bbox=str(gdf.envelope[0])
    polygon=bbox
#    print(bbox)
    #    print(polygon)
else:
    print('Wrong AOI_MODE parameter! Please revise the configuration file')
    sys.exit()

print( polygon)
wkt=polygon
print(wkt)
###################################################################
# QUERYING ASF
print('#########################################################')
print('Quering ASF with the defined parameteres')
results=asf.geo_search(platform=[myplatform],beamMode=[asf.IW],processingLevel=procType,relativeOrbit=TRACK,intersectsWith=wkt,start=START,end=END,maxResults=1000)
print(len(results))

###################################################
# STARTING DOWNLOAD
print('#######################################################')
print('Starting download')
results.download(path=directory,session=session,processes=NPD)

