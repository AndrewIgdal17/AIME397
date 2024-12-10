# This script merges the FERC 1000 regions with the HIFLD transmission lines dataset, and exports the resulting datasets to geojson files.
# It also plots the transmission lines in each of the FERC 1000 regions.

# %%
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

# %% load ferc1000 regions
ferc1000 = gpd.read_file('data/FERC_1000_Regions.geojson')

ferc1000.drop(columns=['NAICS_CODE'], inplace=True)

caiso = ferc1000[ferc1000['FERC_1000 Regions'] == 'CAISO']
ercot = ferc1000[ferc1000['FERC_1000 Regions'] == 'ERCOT']
iso_ne = ferc1000[ferc1000['FERC_1000 Regions'] == 'ISO-NE']
se = ferc1000[ferc1000['FERC_1000 Regions'] == 'SE']
nyiso = ferc1000[ferc1000['FERC_1000 Regions'] == 'NYISO']
pjm = ferc1000[ferc1000['FERC_1000 Regions'] == 'PJM']
miso = ferc1000[ferc1000['FERC_1000 Regions'] == 'MISO']
spp = ferc1000[ferc1000['FERC_1000 Regions'] == 'SPP']



# %%
# in each of the datasets, drop everything except 'FERC_1000 Regions' and 'geometry'
caiso = caiso[['FERC_1000 Regions', 'geometry']]
ercot = ercot[['FERC_1000 Regions', 'geometry']]
iso_ne = iso_ne[['FERC_1000 Regions', 'geometry']]
se = se[['FERC_1000 Regions', 'geometry']]
nyiso = nyiso[['FERC_1000 Regions', 'geometry']]
pjm = pjm[['FERC_1000 Regions', 'geometry']]
miso = miso[['FERC_1000 Regions', 'geometry']]
spp = spp[['FERC_1000 Regions', 'geometry']]

caiso.to_file('data/caisogeometry.geojson', driver='GeoJSON')
ercot.to_file('data/ercotgeometry.geojson', driver='GeoJSON')
iso_ne.to_file('data/iso_negeometry.geojson', driver='GeoJSON')
se.to_file('data/segeometry.geojson', driver='GeoJSON')
nyiso.to_file('data/nyisogeometry.geojson', driver='GeoJSON')
pjm.to_file('data/pjmgeometry.geojson', driver='GeoJSON')
miso.to_file('data/misogeometry.geojson', driver='GeoJSON')
spp.to_file('data/sppgeometry.geojson', driver='GeoJSON')




# %% 
# load hifld transmission lines
transmission = gpd.read_file('data/Electric__Power_Transmission_Lines.geojson')

#ensure that the CRS of the two datasets are the same
transmission = transmission.to_crs(ferc1000.crs)



# %%
# drop 'NAICS_CODE' column from transmission data
transmission.drop(columns=['NAICS_CODE'], inplace=True)
transmission.drop(columns=['NAICS_DESC'], inplace=True)
transmission.drop(columns=['SOURCE'], inplace=True)
transmission.drop(columns=['VAL_METHOD'], inplace=True)
transmission.drop(columns=['INFERRED'], inplace=True)  
transmission.drop(columns=['SUB_1'], inplace=True)
transmission.drop(columns=['SUB_2'], inplace=True)
transmission.drop(columns=['GlobalID'], inplace=True)




# %%
# spacial join, inefficient method but works
transmissioncaiso = gpd.sjoin(transmission, caiso, how='inner', op='intersects')
transmissionercot = gpd.sjoin(transmission, ercot, how='inner', op='intersects')
transmissioniso_ne = gpd.sjoin(transmission, iso_ne, how='inner', op='intersects')
transmissionse = gpd.sjoin(transmission, se, how='inner', op='intersects')
transmissionnyiso = gpd.sjoin(transmission, nyiso, how='inner', op='intersects')
transmissionpjm = gpd.sjoin(transmission, pjm, how='inner', op='intersects')
transmissionmiso = gpd.sjoin(transmission, miso, how='inner', op='intersects')
transmissionspp = gpd.sjoin(transmission, spp, how='inner', op='intersects')

# %%
# export the transmission files to geojson
transmissioncaiso.to_file('data/transmissionCAISO.geojson', driver='GeoJSON')
transmissionercot.to_file('data/transmissionERCOT.geojson', driver='GeoJSON')
transmissioniso_ne.to_file('data/transmissionISO_NE.geojson', driver='GeoJSON')
transmissionse.to_file('data/transmissionSE.geojson', driver='GeoJSON')
transmissionnyiso.to_file('data/transmissionNYISO.geojson', driver='GeoJSON')
transmissionpjm.to_file('data/transmissionPJM.geojson', driver='GeoJSON')
transmissionmiso.to_file('data/transmissionMISO.geojson', driver='GeoJSON')
transmissionspp.to_file('data/transmissionSPP.geojson', driver='GeoJSON')



# %%












