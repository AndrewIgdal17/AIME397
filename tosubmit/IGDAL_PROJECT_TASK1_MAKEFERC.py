# %%
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# The goal of this script is to create a new GeoDataFrame that approximates FERC Order 1000 regions.
# It accomplishes this by aggregating the control areas in the 'Control__Areas.geojson' file
# by the Balancing Authority (BA) they belong to.

# Load the GeoJSON file and filter columns
ba_gdf = gpd.read_file('data/Control__Areas.geojson')

# Define US states of interest
us_states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

state_abbreviations = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA',
    'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
    'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
    'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA',
    'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}

# Filter the GeoDataFrame to include only rows where 'STATE' is in the list of US states
ba_gdf = ba_gdf[ba_gdf['STATE'].isin(us_states)]

# Check the coordinate reference system (CRS) of ba_gdf and unique BA names
print(ba_gdf.crs)
print(ba_gdf['NAME'].unique())


# Load county shapefile and convert to the same CRS as ba_gdf
counties = gpd.read_file('data/US_COUNTY_SHPFILE/US_county_cont.shp')
counties = counties.to_crs(ba_gdf.crs)

# Map state names to abbreviations
counties['STATE_NAME'] = counties['STATE_NAME'].map(state_abbreviations)
# Drop rows with NaN in 'STATE_NAME'
counties = counties.dropna(subset=['STATE_NAME'])

# Read in BA_FERC1000.csv and drop the 'Notes' column
ba_to_ferc_csv = pd.read_csv('data/BA_FERC1000.csv')
ba_to_ferc_csv = ba_to_ferc_csv.drop(columns='Notes')

# Clean up the 'NAME' and 'Balancing Authority' columns
ba_gdf['NAME'] = ba_gdf['NAME'].str.lower().str.strip()
ba_to_ferc_csv['Balancing Authority'] = ba_to_ferc_csv['Balancing Authority'].str.lower().str.strip()

# Merge ba_gdf and ba_to_ferc_csv
ba2_gdf = ba_gdf.merge(ba_to_ferc_csv, how='left', left_on='NAME', right_on='Balancing Authority')

# Exclude 'WestConnect' from 'FERC_1000 Regions'
ba2_gdf = ba2_gdf[~ba2_gdf['FERC_1000 Regions'].isin(['WestConnect'])]



# Exclude NYISO from filtering
non_nyiso = ba2_gdf[ba2_gdf['FERC_1000 Regions'] != 'NYISO']

# Apply filters for valid data to all regions except NYISO
non_nyiso = non_nyiso[
    (non_nyiso['TOTAL_CAP'] >= 0) & (non_nyiso['AVAIL_CAP'] >= 0) &
    (non_nyiso['PEAK_LOAD'] >= 0) & (non_nyiso['MIN_LOAD'] >= 0)
]

# Ensure available capacity is not greater than total capacity
non_nyiso = non_nyiso[non_nyiso['AVAIL_CAP'] <= non_nyiso['TOTAL_CAP']]

# Ensure peak load is greater than or equal to minimum load
non_nyiso = non_nyiso[non_nyiso['PEAK_LOAD'] >= non_nyiso['MIN_LOAD']]

# Drop rows with missing values in critical columns
non_nyiso = non_nyiso.dropna(
    subset=['TOTAL_CAP', 'AVAIL_CAP', 'PEAK_LOAD', 'MIN_LOAD', 'SHAPE__Area', 'SHAPE__Length']
)

# Combine the filtered non-NYISO data back with the NYISO data
nyiso = ba2_gdf[ba2_gdf['FERC_1000 Regions'] == 'NYISO']
ba2_gdf_filtered = pd.concat([non_nyiso, nyiso])

# Group by 'FERC_1000 Regions' and sum the specified columns
ferc1000_avail = ba2_gdf.groupby('FERC_1000 Regions')['AVAIL_CAP'].sum()
ferc1000_totals = ba2_gdf.groupby('FERC_1000 Regions')['TOTAL_CAP'].sum()
ferc1000_peaks = ba2_gdf.groupby('FERC_1000 Regions')['PEAK_LOAD'].sum()
ferc1000_min = ba2_gdf.groupby('FERC_1000 Regions')['MIN_LOAD'].sum()
ferc1000_area = ba2_gdf.groupby('FERC_1000 Regions')['SHAPE__Area'].sum()
ferc1000_length = ba2_gdf.groupby('FERC_1000 Regions')['SHAPE__Length'].sum()

# Dissolve ba2_gdf by 'FERC_1000 Regions'
ferc1000_gdf = ba2_gdf.dissolve(by='FERC_1000 Regions').reset_index()

# Replace columns in ferc1000_gdf with grouped sums
ferc1000_gdf['AVAIL_CAP'] = ferc1000_gdf['FERC_1000 Regions'].map(ferc1000_avail)
ferc1000_gdf['TOTAL_CAP'] = ferc1000_gdf['FERC_1000 Regions'].map(ferc1000_totals)
ferc1000_gdf['PEAK_LOAD'] = ferc1000_gdf['FERC_1000 Regions'].map(ferc1000_peaks)
ferc1000_gdf['MIN_LOAD'] = ferc1000_gdf['FERC_1000 Regions'].map(ferc1000_min)
ferc1000_gdf['SHAPE__Area'] = ferc1000_gdf['FERC_1000 Regions'].map(ferc1000_area)
ferc1000_gdf['SHAPE__Length'] = ferc1000_gdf['FERC_1000 Regions'].map(ferc1000_length)

# Merge SERTP, FRCC, and SCRTP into SE
ferc1000_gdf.loc[ferc1000_gdf['FERC_1000 Regions'] == 'SERTP', 'FERC_1000 Regions'] = 'SE'
ferc1000_gdf.loc[ferc1000_gdf['FERC_1000 Regions'] == 'FRCC', 'FERC_1000 Regions'] = 'SE'
ferc1000_gdf.loc[ferc1000_gdf['FERC_1000 Regions'] == 'SCRTP', 'FERC_1000 Regions'] = 'SE'

# Check for overlapping areas between SPP and SE
spp = ferc1000_gdf[ferc1000_gdf['FERC_1000 Regions'] == 'SPP']
se = ferc1000_gdf[ferc1000_gdf['FERC_1000 Regions'] == 'SE']
spp_se = gpd.overlay(spp, se, how='intersection')
print(spp_se)


# Remove overlapping areas (subtract SPP from SE)
se_without_spp = gpd.overlay(se, spp, how='difference')

# Update the SE region with the new geometry
ferc1000_gdf.loc[ferc1000_gdf['FERC_1000 Regions'] == 'SE', 'geometry'] = se_without_spp['geometry']

# Manually add missing counties in FL, SC, AL, and TN to the SE region
fl_counties = counties[counties['STATE_NAME'].str.lower() == 'fl']
sc_counties = counties[counties['STATE_NAME'].str.lower() == 'sc']
al_counties = counties[counties['STATE_NAME'].str.lower() == 'al']

tn_counties = counties[counties['STATE_NAME'].str.lower() == 'tn']
monroe = tn_counties[tn_counties['NAME'].str.lower() == 'monroe']
blount = tn_counties[tn_counties['NAME'].str.lower() == 'blount']
sevier = tn_counties[tn_counties['NAME'].str.lower() == 'sevier']

# Dissolve counties into single geometries
fl_geometry = fl_counties.dissolve(by='STATE_NAME')['geometry'].iloc[0]
sc_geometry = sc_counties.dissolve(by='STATE_NAME')['geometry'].iloc[0]
al_geometry = al_counties.dissolve(by='STATE_NAME')['geometry'].iloc[0]

monroe_geometry = monroe.dissolve(by='STATE_NAME')['geometry'].iloc[0]
blount_geometry = blount.dissolve(by='STATE_NAME')['geometry'].iloc[0]
sevier_geometry = sevier.dissolve(by='STATE_NAME')['geometry'].iloc[0]

# Union the geometries
m_b_union = monroe_geometry.union(blount_geometry)
m_b_s_union = m_b_union.union(sevier_geometry)

fl_sc_union = fl_geometry.union(sc_geometry)
fl_sc_al_union = fl_sc_union.union(al_geometry)
fl_sc_al_mbs_union = fl_sc_al_union.union(m_b_s_union)

# Merge the new geometries into the SE region
se_geometry = se_without_spp.unary_union
se_updated_geometry = se_geometry.union(fl_sc_al_mbs_union)

# Update the SE region with the combined geometry
ferc1000_gdf.loc[ferc1000_gdf['FERC_1000 Regions'] == 'SE', 'geometry'] = se_updated_geometry

# Drop regions not of interest
ferc1000_gdf = ferc1000_gdf[ferc1000_gdf['FERC_1000 Regions'].isin(
    ['SE', 'NYISO', 'ERCOT', 'CAISO', 'MISO', 'ISO-NE', 'PJM', 'SPP']
)]

# Dissolve to ensure proper geometry
ferc1000_gdf = ferc1000_gdf.dissolve(by='FERC_1000 Regions').reset_index()

# Print columns and first 5 rows
print(ferc1000_gdf.columns)
print(ferc1000_gdf.head())

# Prepare state borders for plotting
state_borders = counties.dissolve(by='STATE_NAME').reset_index()
state_borders = state_borders[state_borders['STATE_NAME'].isin(us_states)]
state_borders = state_borders.to_crs(ferc1000_gdf.crs)


print(ferc1000_gdf['FERC_1000 Regions'].unique())



# Define region colors for plotting
regions = ferc1000_gdf['FERC_1000 Regions'].unique()
region_colors = {
    'CAISO': '#ffcc00',   # California ISO
    'ERCOT': '#bf5700',   # Electric Reliability Council of Texas
    'ISO-NE': '#8a2be2',  # ISO New England
    'SE': '#00bfff',      # The Southeast
    'NYISO': '#ff0000',   # New York ISO
    'PJM': '#228b22',     # PJM Interconnection
    'MISO': '#ff69b4',    # Midcontinent ISO
    'SPP': '#ff8c00'      # Southwest Power Pool
}

# Create legend patches
legend_patches = []
for region, color in region_colors.items():
    patch = mpatches.Patch(color=color, label=region)
    legend_patches.append(patch)

# Plotting
fig, ax = plt.subplots(1, 1, figsize=(15, 10))

# Plot each region
for region in regions:
    ferc1000_gdf[ferc1000_gdf['FERC_1000 Regions'] == region].plot(
        ax=ax,
        color=region_colors.get(region, '#cccccc'),
        edgecolor='black'
    )

# Plot state borders
state_borders.boundary.plot(ax=ax, color='black', linewidth=0.5)

# Add title and labels
plt.title('FERC Order 1000 Regions', fontsize=20)
plt.xlabel('Longitude', fontsize=15)
plt.ylabel('Latitude', fontsize=15)

# Add legend
plt.legend(handles=legend_patches, loc='lower left', fontsize=12)

# Save and show the figure
plt.savefig('FERC_1000_Regions.png', dpi=300)
plt.savefig('FERC_1000_Regions.pdf')
plt.show()



# Drop unnecessary columns
ferc1000_gdf.drop(columns=[
    'NAME', 'ADDRESS', 'CITY', 'STATE', 'ZIP', 'TELEPHONE',
    'COUNTRY', 'WEBSITE', 'Balancing Authority', 'DOE_HGM Region'
], inplace=True)

# %%

# Save ferc1000_gdf to a new GeoJSON file
ferc1000_gdf.to_file('data/FERC_1000_Regions.geojson', driver='GeoJSON')

