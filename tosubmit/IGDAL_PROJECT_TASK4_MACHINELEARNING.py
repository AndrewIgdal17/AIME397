# This script processes merged transmission data, integrates ACS demographic data at the region level,
# performs hierarchical clustering, and visualizes the results including a dendrogram and correlation heatmaps.

# %% Import Libraries
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import censusdata
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.metrics import silhouette_score
import seaborn as sns

# %% Load Merged Transmission Data
merged_caiso = gpd.read_file('data/mergedtransmissionCAISO.geojson')
merged_ercot = gpd.read_file('data/mergedtransmissionERCOT.geojson')
merged_isone = gpd.read_file('data/mergedtransmissionISONE.geojson')
merged_miso = gpd.read_file('data/mergedtransmissionMISO.geojson')
merged_nyiso = gpd.read_file('data/mergedtransmissionNYISO.geojson')
merged_pjm = gpd.read_file('data/mergedtransmissionPJM.geojson')
merged_spp = gpd.read_file('data/mergedtransmissionSPP.geojson')
merged_se = gpd.read_file('data/mergedtransmissionSE.geojson')

regions = {
    'CAISO': merged_caiso,
    'ERCOT': merged_ercot,
    'ISONE': merged_isone,
    'MISO': merged_miso,
    'NYISO': merged_nyiso,
    'PJM': merged_pjm,
    'SPP': merged_spp,
    'SE': merged_se
}

# %% Load Region Geometries
caiso_geometry = gpd.read_file('data/caisogeometry.geojson')
ercot_geometry = gpd.read_file('data/ercotgeometry.geojson')
isone_geometry = gpd.read_file('data/iso_negeometry.geojson')
miso_geometry = gpd.read_file('data/misogeometry.geojson')
nyiso_geometry = gpd.read_file('data/nyisogeometry.geojson')
pjm_geometry = gpd.read_file('data/pjmgeometry.geojson')
spp_geometry = gpd.read_file('data/sppgeometry.geojson')
se_geometry = gpd.read_file('data/segeometry.geojson')

region_geometries = {
    'CAISO': caiso_geometry,
    'ERCOT': ercot_geometry,
    'ISONE': isone_geometry,
    'MISO': miso_geometry,
    'NYISO': nyiso_geometry,
    'PJM': pjm_geometry,
    'SPP': spp_geometry,
    'SE': se_geometry
}

# %% Fetch ACS Data
acs_variables = {
    'Total_Population': 'B01003_001E',
    'Median_Age': 'B01002_001E',
    'Median_Household_Income': 'B19013_001E',
    'White_Population': 'B02001_002E',
    'Black_Population': 'B02001_003E',
    'Asian_Population': 'B02001_005E',
    'Hispanic_Population': 'B03003_003E'
}

acs_data = censusdata.download(
    src='acs5',
    year=2019,
    geo=censusdata.censusgeo([('state', '*'), ('county', '*')]),
    var=list(acs_variables.values())
)

acs_data.columns = acs_variables.keys()
acs_data = acs_data.reset_index()

def extract_geoid(censusgeo):
    geos = censusgeo.geo
    state_fips = geos[0][1]
    county_fips = geos[1][1]
    return state_fips + county_fips

acs_data['GEOID'] = acs_data['index'].apply(extract_geoid)

# %% Get Geometry for Counties
counties = gpd.read_file('data/US_COUNTY_SHPFILE/US_COUNTY_cont.shp')
counties['GEOID'] = counties['STATE_FIPS'] + counties['CNTY_FIPS']

# Merge ACS data with county geometries
acs_gdf = counties.merge(acs_data, on='GEOID')

# %% Process and Clean Data
acs_gdf = acs_gdf.dropna(subset=acs_variables.keys())
acs_gdf = acs_gdf[acs_gdf['Total_Population'] > 0]

acs_gdf['Percent_White'] = (acs_gdf['White_Population'] / acs_gdf['Total_Population']) * 100
acs_gdf['Percent_Black'] = (acs_gdf['Black_Population'] / acs_gdf['Total_Population']) * 100
acs_gdf['Percent_Asian'] = (acs_gdf['Asian_Population'] / acs_gdf['Total_Population']) * 100
acs_gdf['Percent_Hispanic'] = (acs_gdf['Hispanic_Population'] / acs_gdf['Total_Population']) * 100

acs_gdf = acs_gdf[['GEOID', 'Total_Population', 'Median_Age', 'Median_Household_Income',
                   'White_Population', 'Black_Population', 'Asian_Population', 'Hispanic_Population',
                   'Percent_White', 'Percent_Black', 'Percent_Asian', 'Percent_Hispanic', 'geometry']]

# %% Collect All Unique TYPES Across All Regions
all_unique_types = set()
for transmission_data in regions.values():
    if 'TYPE' in transmission_data.columns:
        all_unique_types.update(transmission_data['TYPE'].dropna().unique())
all_unique_types = sorted(all_unique_types)

# %% Define summarize_region Function
def summarize_region(region_name, region_geometry, transmission_data, acs_gdf, all_unique_types):
    region_geometry = region_geometry.to_crs(acs_gdf.crs)
    transmission_data = transmission_data.to_crs(acs_gdf.crs)
    counties_in_region = gpd.sjoin(acs_gdf, region_geometry, how='inner', op='intersects')

    if counties_in_region.empty:
        total_population = median_age = median_household_income = np.nan
        percent_white = percent_black = percent_asian = percent_hispanic = np.nan
    else:
        total_population = counties_in_region['Total_Population'].sum()
        if total_population == 0:
            total_population = np.nan
        median_age = np.average(counties_in_region['Median_Age'], weights=counties_in_region['Total_Population'])
        median_household_income = np.average(counties_in_region['Median_Household_Income'], weights=counties_in_region['Total_Population'])
        percent_white = (counties_in_region['White_Population'].sum() / total_population) * 100
        percent_black = (counties_in_region['Black_Population'].sum() / total_population) * 100
        percent_asian = (counties_in_region['Asian_Population'].sum() / total_population) * 100
        percent_hispanic = (counties_in_region['Hispanic_Population'].sum() / total_population) * 100

    total_power_capacity = transmission_data['POWER_CAPACITY'].sum() if 'POWER_CAPACITY' in transmission_data.columns else np.nan
    total_line_length_mi = transmission_data['LINE_LENGTH_MILES'].sum() if 'LINE_LENGTH_MILES' in transmission_data.columns else np.nan

    if 'TYPE' in transmission_data.columns:
        type_counts = transmission_data['TYPE'].value_counts()
        type_counts_dict = {t: int(type_counts.get(t, 0)) for t in all_unique_types}
    else:
        type_counts_dict = {t: 0 for t in all_unique_types}

    region_summary = {
        'Region': region_name,
        'Total_Population': total_population,
        'Median_Age': median_age,
        'Median_Household_Income': median_household_income,
        'Percent_White': percent_white,
        'Percent_Black': percent_black,
        'Percent_Asian': percent_asian,
        'Percent_Hispanic': percent_hispanic,
        'Total_Power_Capacity': total_power_capacity,
        'Total_Line_Length_MI': total_line_length_mi
    }
    region_summary.update(type_counts_dict)
    return region_summary

# %% Summarize Each Region
region_summaries = []
for region_name in regions.keys():
    transmission_data = regions[region_name]
    region_geometry = region_geometries[region_name]
    summary = summarize_region(region_name, region_geometry, transmission_data, acs_gdf, all_unique_types)
    region_summaries.append(summary)

summary_df = pd.DataFrame(region_summaries)
summary_df.fillna(0, inplace=True)
print(summary_df)

# %% Standardize Data
numeric_columns = summary_df.select_dtypes(include=np.number).columns
scaler = StandardScaler()
standardized_data = scaler.fit_transform(summary_df[numeric_columns])
standardized_df = pd.DataFrame(standardized_data, columns=numeric_columns)

# %% Hierarchical Clustering
linkage_matrix = linkage(standardized_data, method='ward')

plt.figure(figsize=(10, 7))
plt.title("Dendrogram for Hierarchical Clustering")
dendrogram(linkage_matrix, labels=summary_df['Region'].values, leaf_rotation=90, leaf_font_size=10)
plt.xlabel('Regions')
plt.ylabel('Distance')
plt.savefig('dendrogram.png', dpi=1200)
plt.show()

# %% Correlation Matrix Heatmap
correlation_matrix = summary_df[numeric_columns].corr()

plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title('Correlation Matrix Heatmap')
plt.xticks(rotation=45)
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=1200)
plt.show()

# %% Clustered Heatmap of Regions
standardized_df['Region'] = summary_df['Region']
standardized_df.set_index('Region', inplace=True)

sns.clustermap(standardized_df, method='ward', cmap='coolwarm', figsize=(12, 10))
plt.title('Clustered Heatmap of Regions')
plt.savefig('clustered_heatmap.png', dpi=1200)
plt.show()


# %%