import os
import shutil
import json
from pathlib import Path

def process(collection, catalog_config, endpoint_config, collection_config):
    """
    Custom handler to copy GeoJSON files to the build directory
    and make them available as overlay layers.
    """
    
    # Get the source GeoJSON file path from collection config
    geojson_source = collection_config.get('geojson_source')
    if not geojson_source:
        return collection
    
    # Get the build directory from the catalog config
    build_dir = catalog_config.get('build_dir', 'build')
    catalog_id = catalog_config.get('id', 'catalog')
    
    # Create the data directory in build folder
    data_dir = Path(build_dir) / catalog_id / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the filename from the source path
    source_file = Path(geojson_source)
    destination_file = data_dir / source_file.name
    
    # Copy the GeoJSON file to build directory
    if source_file.exists():
        shutil.copy2(source_file, destination_file)
        print(f"Copied {source_file} to {destination_file}")
        
        # Add the overlay information to the collection
        if 'overlays' not in collection:
            collection['overlays'] = []
        
        overlay_info = {
            'id': f"{collection_config.get('Name', 'overlay')}_geojson",
            'name': collection_config.get('overlay_name', f"{collection_config.get('Name', 'Data')} Overlay"),
            'url': f'data/{source_file.name}',
            'protocol': 'geojson',
            'visible': collection_config.get('overlay_visible', False),
            'style': collection_config.get('overlay_style', {
                'fillColor': '#ff7800',
                'fillOpacity': 0.7,
                'color': '#000',
                'weight': 2,
                'opacity': 1
            })
        }
        
        collection['overlays'].append(overlay_info)
    else:
        print(f"Warning: GeoJSON file {source_file} not found")
    
    return collection