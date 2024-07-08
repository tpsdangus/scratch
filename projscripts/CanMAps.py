import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import folium
import os

def filter_polygons_within_distance(input_shapefile, output_shapefile, output_excel, center_point, max_distance_km):
    # Load the shapefile
    gdf = gpd.read_file(input_shapefile)
    
    # Ensure the CRS is defined and set to WGS84 if not
    if gdf.crs is None:
        print(f"Warning: CRS is not defined for {input_shapefile}. Assuming WGS84 (EPSG:4326).")
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)
    
    # Filter out polygons where 'type3' is "Water body"
    gdf = gdf[gdf['Type_3'] != 'Water body']
    
    # Create a GeoDataFrame for the center point
    center_gdf = gpd.GeoDataFrame([{'geometry': center_point}], crs="EPSG:4326")
    
    # Reproject to a projected CRS (e.g., EPSG:3857) for distance calculation
    gdf_projected = gdf.to_crs(epsg=3857)
    center_gdf_projected = center_gdf.to_crs(epsg=3857)
    
    # Buffer the center point by the max distance in meters (500 km)
    center_buffer = center_gdf_projected.buffer(max_distance_km * 1000).iloc[0]
    
    # Filter polygons that are completely within the buffer
    polygons_within_distance = gdf_projected[gdf_projected.geometry.within(center_buffer)]
    
    # Reproject back to the original CRS (WGS84)
    polygons_within_distance = polygons_within_distance.to_crs(epsg=4326)
    
    # Check if any polygons were found
    if polygons_within_distance.empty:
        print(f"No polygons found within {max_distance_km} km of the center point.")
        return
    
    # Save the filtered polygons to a new shapefile
    polygons_within_distance.to_file(output_shapefile, driver='ESRI Shapefile')
    
    # Save the attribute data to an Excel file
    polygons_within_distance.drop(columns='geometry').to_excel(output_excel, index=False)
    
    print(f"Filtered polygons saved to {output_shapefile}")
    print(f"Attribute data saved to {output_excel}")
    
    # Create and save a map for the filtered polygons
    create_map_from_shapefile(output_shapefile, os.path.dirname(output_shapefile))

def create_map_from_shapefile(shapefile_path, output_folder):
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)
    
    # Ensure the CRS is defined and set to WGS84 if not
    if gdf.crs is None:
        print(f"Warning: CRS is not defined for {shapefile_path}. Assuming WGS84 (EPSG:4326).")
        gdf.set_crs(epsg=4326, inplace=True)
    
    # Get the centroid of the geometries to center the map
    centroid = gdf.geometry.centroid
    mean_lat = centroid.y.mean()
    mean_lon = centroid.x.mean()
    
    # Create a folium map centered at the centroid
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=10)
    
    # Add the GeoDataFrame to the map
    folium.GeoJson(gdf).add_to(m)
    
    # Save the map as an HTML file
    output_file = os.path.join(output_folder, os.path.basename(shapefile_path).replace('.shp', '.html'))
    m.save(output_file)
    
    print(f"Map saved to {output_file}")

# Define the input shapefile and output file paths
input_shapefile = 'maps/gadm41_CAN_shp/gadm41_CAN_3.shp'
output_shapefile = 'maps/gadm41_CAN_shp/GTA.shp'
output_excel = 'maps/gadm41_CAN_shp/GTA_attributes.xlsx'

# Define the center point (Toronto City Hall) and the max distance in km
toronto_city_hall = Point(-79.3849, 43.6529)
max_distance_km = 500

# Filter polygons within the specified distance and save the results
filter_polygons_within_distance(input_shapefile, output_shapefile, output_excel, toronto_city_hall, max_distance_km)
