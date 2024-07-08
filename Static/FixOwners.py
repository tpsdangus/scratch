import json

# Path to the files
geojson_file_path = '../static/filtered_cells.geojson'
output_geojson_path = '../static/updated_filtered_cells.geojson'

# Load the GeoJSON file
with open(geojson_file_path, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Update each feature in the GeoJSON data
for feature in geojson_data['features']:
    properties = feature['properties']
    
    # Move the 'owner' property under 'properties'
    if 'owner' in feature:
        properties['owner'] = feature.pop('owner')
    
    # Remove the 'samples' and 'unit' properties if they exist
    properties.pop('samples', None)
    properties.pop('unit', None)

# Save the updated GeoJSON data to a new file
with open(output_geojson_path, 'w', encoding='utf-8') as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=4)

print(f"Updated GeoJSON file created at: {output_geojson_path}")
