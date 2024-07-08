import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

# Path to the CSV and GeoJSON files
csv_file_path = '../static/Cells20220707.csv'
geojson_file_path = '../static/NorthEastCells.geojson'
output_geojson_path = '../static/filtered_cells.geojson'

# Load the GeoJSON file containing the polygon
polygon = gpd.read_file(geojson_file_path)

# Function to check if a point is within the polygon
def is_within_polygon(lat, lon, polygon):
    point = Point(lon, lat)
    return polygon.contains(point).any()

# Initialize a list to collect features for the new GeoJSON
features = []
total_rows_processed = 0

# Process the CSV file in chunks
chunk_size = 10000  # Adjust chunk size based on available memory
for chunk_number, chunk in enumerate(pd.read_csv(csv_file_path, chunksize=chunk_size)):
    # Check each row in the chunk
    chunk['within_polygon'] = chunk.apply(lambda row: is_within_polygon(row['lat'], row['lon'], polygon), axis=1)
    
    # Filter rows that are within the polygon
    filtered_chunk = chunk[chunk['within_polygon']]
    
    # Convert filtered rows to GeoJSON features, excluding the last five columns
    columns_to_include = chunk.columns[:-5].difference(['lat', 'lon', 'within_polygon'])
    for _, row in filtered_chunk.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']]
            },
            'properties': {col: row[col] for col in columns_to_include}
        }
        features.append(feature)
    
    # Update total rows processed
    total_rows_processed += len(chunk)

# Create the final GeoJSON structure
geojson_data = {
    'type': 'FeatureCollection',
    'features': features
}

# Write the final GeoJSON to a file
with open(output_geojson_path, 'w', encoding='utf-8') as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=4)

print(f"GeoJSON file created at: {output_geojson_path}")
print(f"Total rows processed: {total_rows_processed}")
