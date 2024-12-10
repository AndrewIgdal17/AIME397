# This script processes transmission line data, merges it with region geometries,
# calculates line lengths and power capacity for AC lines, and provides basic data summaries.
# %%
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from shapely.ops import linemerge, unary_union
from shapely.geometry import LineString, MultiLineString, GeometryCollection

# Load and reproject transmission data for each FERC region
transmissionCAISO = gpd.read_file('data/transmissionCAISO.geojson').to_crs(epsg=3857)
transmissionERCOT = gpd.read_file('data/transmissionERCOT.geojson').to_crs(epsg=3857)
transmissionISONE = gpd.read_file('data/transmissionISO_NE.geojson').to_crs(epsg=3857)
transmissionSE = gpd.read_file('data/transmissionSE.geojson').to_crs(epsg=3857)
transmissionNYISO = gpd.read_file('data/transmissionNYISO.geojson').to_crs(epsg=3857)
transmissionPJM = gpd.read_file('data/transmissionPJM.geojson').to_crs(epsg=3857)
transmissionMISO = gpd.read_file('data/transmissionMISO.geojson').to_crs(epsg=3857)
transmissionSPP = gpd.read_file('data/transmissionSPP.geojson').to_crs(epsg=3857)

regions = {
    'CAISO': transmissionCAISO,
    'ERCOT': transmissionERCOT,
    'ISONE': transmissionISONE,
    'SE': transmissionSE,
    'NYISO': transmissionNYISO,
    'PJM': transmissionPJM,
    'MISO': transmissionMISO,
    'SPP': transmissionSPP
}

# Load and reproject region geometries
caiso = gpd.read_file('data/caisogeometry.geojson').to_crs(epsg=3857)
ercot = gpd.read_file('data/ercotgeometry.geojson').to_crs(epsg=3857)
isone = gpd.read_file('data/iso_negeometry.geojson').to_crs(epsg=3857)
se = gpd.read_file('data/segeometry.geojson').to_crs(epsg=3857)
nyiso = gpd.read_file('data/nyisogeometry.geojson').to_crs(epsg=3857)
pjm = gpd.read_file('data/pjmgeometry.geojson').to_crs(epsg=3857)
miso = gpd.read_file('data/misogeometry.geojson').to_crs(epsg=3857)
spp = gpd.read_file('data/sppgeometry.geojson').to_crs(epsg=3857)

# %%
# plot the transmission lines in CAISO
fig, ax = plt.subplots(figsize=(10, 10))
transmissionCAISO.plot(ax=ax)
caiso.boundary.plot(ax=ax, color='red')
plt.title('CAISO and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# plot the transmission lines in ERCOT
fig, ax = plt.subplots(figsize=(10, 10))
transmissionERCOT.plot(ax=ax)
ercot.boundary.plot(ax=ax, color='red')
plt.title('ERCOT and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# plot the transmission lines in ISO-NE
fig, ax = plt.subplots(figsize=(10, 10))
transmissionISONE.plot(ax=ax)
isone.boundary.plot(ax=ax, color='red')
plt.title('ISO-NE and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# plot the transmission lines in SE
fig, ax = plt.subplots(figsize=(10, 10))
transmissionSE.plot(ax=ax)
se.boundary.plot(ax=ax, color='red')
plt.title('SE and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# plot the transmission lines in NYISO
fig, ax = plt.subplots(figsize=(10, 10))
transmissionNYISO.plot(ax=ax)
nyiso.boundary.plot(ax=ax, color='red')
plt.title('NYISO and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# plot the transmission lines in PJM
fig, ax = plt.subplots(figsize=(10, 10))
transmissionPJM.plot(ax=ax)
pjm.boundary.plot(ax=ax, color='red')
plt.title('PJM and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

# plot the transmission lines in MISO
fig, ax = plt.subplots(figsize=(10, 10))
transmissionMISO.plot(ax=ax)
miso.boundary.plot(ax=ax, color='red')
plt.title('MISO and Its Transmission Lines')
plt.xlabel('Longitude')
plt.show()

# plot the transmission lines in SPP
fig, ax = plt.subplots(figsize=(10, 10))
transmissionSPP.plot(ax=ax)
spp.boundary.plot(ax=ax, color='red')
plt.title('SPP and Its Transmission Lines')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()
# %%


def column_rename(df):
    df.rename(columns={
        'SOURCEDATE_left': 'SOURCEDATE_TRANS',
        'SOURCEDATE_right': 'SOURCEDATE_CA',
        'VAL_DATE_left': 'VAL_DATE_TRANS',
        'VAL_DATE_right': 'VAL_DATE_CA',
        'ID_left': 'ID_TRANS',
        'OBJECTID_left': 'OBJECTID_TRANS',
        'OBJECTID_right': 'OBJECTID_CA',
        'ID_right': 'ID_CA'
    }, inplace=True)
    return df

for region, transmission in regions.items():
    column_rename(transmission)
    if 'index_right' in transmission.columns:
        transmission.drop(columns=['index_right'], inplace=True)

def add_year_column(df):
    df['SOURCEDATE'] = pd.to_datetime(df['SOURCEDATE'])
    df['YEAR'] = df['SOURCEDATE'].dt.year
    return df

for region, transmission in regions.items():
    add_year_column(transmission)

def estimate_power_capacity(df):
    """
    Estimate power capacity for AC lines based on line length and voltage.
    """
    psr = 0.327  # ohm/km
    df['LINE_LENGTH_KM'] = df['geometry'].length / 1000
    df['LINE_LENGTH_MILES'] = df['LINE_LENGTH_KM'] * 0.621371
    ac_lines = df['TYPE'].str.contains("AC", na=False)
    e_o = (df.loc[ac_lines, 'VOLTAGE'].astype(float) ** 2) * np.sin(30 * np.pi / 180)
    df.loc[ac_lines, 'POWER_CAPACITY'] = e_o / (df.loc[ac_lines, 'LINE_LENGTH_KM'] * psr)
    df.loc[ac_lines, 'LOG_POWER_CAPACITY'] = np.log(df.loc[ac_lines, 'POWER_CAPACITY'].replace(0, np.nan))
    return df

for region, transmission in regions.items():
    regions[region] = estimate_power_capacity(transmission)
    # Remove lines with negative voltage
    drop_idx = regions[region][regions[region]['VOLTAGE'] < 0].index
    regions[region].drop(drop_idx, inplace=True)

def inspect_data(df):
    print(df.info())
    print(df.head())
    print(df.describe())
    print(df.columns)
    print(df.shape)

for region, transmission in regions.items():
    print(f"Inspecting data for {region}")
    inspect_data(transmission)

def summarize_and_visualize_columns(df, columns_of_interest, region_name):
    for column in columns_of_interest:
        print(f"Summary for {column} in {region_name}")
        if column not in df.columns:
            print(f"{column} not found.")
            continue
        print("Value Counts:")
        print(df[column].value_counts(dropna=False))
        print(f"Unique values: {df[column].nunique()}")

        if pd.api.types.is_numeric_dtype(df[column]):
            summary = df[column].describe()[['mean', 'std', 'min', '25%', '50%', '75%', 'max']]
            print(summary)
            # Hist & Boxplot
            plt.figure(figsize=(14, 6))
            plt.subplot(1, 2, 1)
            sns.histplot(df[column].dropna(), kde=True, bins=30)
            plt.title(f'{column} Distribution - {region_name}')

            plt.subplot(1, 2, 2)
            sns.boxplot(x=df[column].dropna())
            plt.title(f'{column} Boxplot - {region_name}')
            plt.show()

            # KDE
            plt.figure(figsize=(7, 4))
            sns.kdeplot(df[column].dropna(), shade=True)
            plt.title(f'{column} KDE - {region_name}')
            plt.show()

            # CDF
            plt.figure(figsize=(7, 4))
            sns.ecdfplot(df[column].dropna())
            plt.title(f'{column} CDF - {region_name}')
            plt.show()

        else:
            summary = df[column].describe()
            print(summary)
            # Countplot
            plt.figure(figsize=(10, 6))
            sns.countplot(y=df[column], order=df[column].value_counts().index)
            plt.title(f'{column} Count - {region_name}')
            plt.show()

            # Pie chart
            plt.figure(figsize=(6, 6))
            df[column].value_counts().plot.pie(autopct='%1.1f%%')
            plt.title(f'{column} Pie - {region_name}')
            plt.ylabel('')
            plt.show()

        print("=" * 40)

columns_of_interest = ['VOLTAGE', 'STATUS', 'TYPE', 'YEAR', 'LOG_POWER_CAPACITY', 'LINE_LENGTH_MILES']

for region, transmission in regions.items():
    summarize_and_visualize_columns(transmission, columns_of_interest, region)
    transmission.to_crs(epsg=4326, inplace=True)
    transmission.to_file(f'{region}_processed.geojson', driver='GeoJSON')

def merge_lines(transmission_gdf):
    """
    Merge lines based on intersection, owner, voltage, and compatible types.
    """
    transmission_gdf = transmission_gdf.copy()
    transmission_gdf['geometry'] = transmission_gdf['geometry'].apply(
        lambda geom: geom if geom.is_valid else geom.buffer(0)
    )

    def get_line_type(type_str):
        if pd.isnull(type_str):
            return None
        if 'AC' in type_str:
            return 'AC'
        elif 'DC' in type_str:
            return 'DC'
        return None

    transmission_gdf['LINE_TYPE'] = transmission_gdf['TYPE'].apply(get_line_type)
    sindex = transmission_gdf.sindex
    merged_geometries = []
    processed_indices = set()

    for idx, line in transmission_gdf.iterrows():
        if idx in processed_indices:
            continue

        try:
            possible_matches_index = list(sindex.intersection(line.geometry.bounds))
            possible_matches = transmission_gdf.iloc[possible_matches_index]
            matches = possible_matches[
                (possible_matches['OWNER'] == line['OWNER']) &
                (possible_matches['VOLTAGE'] == line['VOLTAGE']) &
                (possible_matches['LINE_TYPE'] == line['LINE_TYPE'])
            ]
            matches = matches[matches.geometry.intersects(line.geometry)]
            if matches.empty:
                continue

            match_indices = matches.index.tolist()
            processed_indices.update(match_indices)

            line_geometries = []
            for geom in matches.geometry:
                if geom.geom_type == 'LineString':
                    line_geometries.append(geom)
                elif geom.geom_type == 'MultiLineString':
                    line_geometries.extend(geom.geoms)

            if not line_geometries:
                continue

            if len(line_geometries) == 1:
                merged_geom = line_geometries[0]
            else:
                united = unary_union(line_geometries)
                if isinstance(united, (LineString, MultiLineString)):
                    merged_geom = linemerge(united)
                elif isinstance(united, GeometryCollection):
                    lines_in_collection = [g for g in united.geoms if isinstance(g, (LineString, MultiLineString))]
                    merged_geom = linemerge(MultiLineString(lines_in_collection)) if lines_in_collection else None
                else:
                    merged_geom = None

            if merged_geom is None or merged_geom.is_empty:
                continue

            merged_types = matches['TYPE'].unique()
            merged_types_str = ', '.join(merged_types)
            unique_types = set(merged_types)
            if len(unique_types) == 1:
                merged_type = unique_types.pop()
            else:
                line_type = line['LINE_TYPE']
                if all(line_type in t for t in merged_types if pd.notnull(t)):
                    merged_type = line_type
                else:
                    continue

            merged_geometries.append({
                'OWNER': line['OWNER'],
                'VOLTAGE': line['VOLTAGE'],
                'TYPE': merged_type,
                'MERGED_TYPES': merged_types_str,
                'geometry': merged_geom
            })

        except Exception as e:
            print(f"Warning: Could not merge lines OWNER={line['OWNER']}, VOLTAGE={line['VOLTAGE']}: {e}")
            continue

    return gpd.GeoDataFrame(merged_geometries, crs=transmission_gdf.crs)

merged_regions = {}
for region, transmission in regions.items():
    merged_transmission = merge_lines(transmission)
    merged_regions[region] = merged_transmission

for region_name, merged_transmission in merged_regions.items():
    merged_transmission.to_crs(epsg=3857, inplace=True)
    merged_transmission['LINE_LENGTH_KM'] = merged_transmission['geometry'].length / 1000
    merged_transmission['LINE_LENGTH_MILES'] = merged_transmission['LINE_LENGTH_KM'] * 0.621371
    merged_transmission = estimate_power_capacity(merged_transmission)
    merged_regions[region_name] = merged_transmission
    output_filename = f"data/mergedtransmission{region_name}.geojson"
    merged_transmission.to_crs(epsg=4326, inplace=True)
    merged_transmission.to_file(output_filename, driver='GeoJSON')

