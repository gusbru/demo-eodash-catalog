import logging
from datetime import datetime

from pystac import Asset, Collection, Item, Link


def process(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Custom handler that processes YAML TimeEntries and ensures XYZ links are created for Titiler"""
    
    # Extract parameters
    bbox = endpoint_config.get("Bbox", [-115.2, 32.0, -114.0, 33.2])
    time_entries = endpoint_config.get("TimeEntries", [])
    
    if not time_entries:
        logging.warning("No TimeEntries found in endpoint_config")
        return collection
    
    # Process each time entry from YAML
    for time_entry in time_entries:
        time_str = time_entry.get("Time")
        assets = time_entry.get("Assets", [])
        links = time_entry.get("Links", [])
        
        if not time_str:
            logging.warning("No Time found in time entry")
            continue
            
        # Parse datetime
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        # Create STAC Item
        item = Item(
            id=time_str,  # Use the original time string as ID to match EODash expectations
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]]
                ]]
            },
            bbox=bbox,
            datetime=dt,
            properties={}
        )
        
        # Add assets from YAML
        for asset_config in assets:
            identifier = asset_config.get("Identifier", "data")
            file_href = asset_config.get("File")
            
            if file_href:
                item.add_asset(
                    identifier,
                    Asset(
                        href=file_href,
                        media_type="image/tiff",
                        roles=["data"]
                    )
                )
        
        # Add links from YAML - this is the key part!
        for link_config in links:
            relation = link_config.get("Relation")
            url = link_config.get("URL")
            link_type = link_config.get("Type", "image/png")
            title = link_config.get("Title", "")
            
            if relation == "xyz" and url:
                # Create XYZ link for map tiles (like aircraft_detection)
                item.add_link(
                    Link(
                        rel="xyz",
                        target=url,
                        media_type=link_type,
                        title=title
                    )
                )
                
                # CRITICAL: Also add a "data" asset with the Titiler URL (like aircraft_detection)
                item.add_asset(
                    "data",
                    Asset(
                        href=url,
                        media_type=link_type,
                        roles=["data"],
                        extra_fields={
                            "proj:epsg": 3857  # Match aircraft_detection
                        }
                    )
                )
                
                logging.info(f"Added XYZ link and data asset for {time_str}: {url}")
        
        # Add item to collection
        collection.add_item(item)
        logging.info(f"Added time series item: {time_str}")
    
    return collection
