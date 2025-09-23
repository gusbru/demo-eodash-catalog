import logging
from datetime import datetime

from pystac import Asset, Collection, Item, Link


def process(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Handler that recreates standard YAML TimeEntries processing with XYZ links added"""
    
    bbox = endpoint_config.get("Bbox", [-180, -90, 180, 90])
    time_entries = endpoint_config.get("TimeEntries", [])
    
    if not time_entries:
        logging.warning("No TimeEntries found in endpoint_config")
        return collection
    
    # Clear any existing items and child collections to avoid duplication
    collection.clear_items()
    # Remove any child links to prevent nested structure
    collection.links = [link for link in collection.links if link.rel != "child"]
    
    # Track min/max times for temporal extent
    min_time = None
    max_time = None
    
    # Process each time entry and create STAC items (like original YAML processing)
    for time_entry in time_entries:
        time_str = time_entry.get("Time")
        assets_config = time_entry.get("Assets", [])
        links_config = time_entry.get("Links", [])
        
        if not time_str:
            continue
            
        try:
            # Parse the time
            entry_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            
            # Track min/max times
            if min_time is None or entry_time < min_time:
                min_time = entry_time
            if max_time is None or entry_time > max_time:
                max_time = entry_time
            
            # Create STAC item (exactly like original processing)
            item = Item(
                id=time_str,  # Use time string as ID
                geometry={
                    "type": "Polygon",
                    "coordinates": [[[bbox[0], bbox[1]], [bbox[2], bbox[1]], 
                                   [bbox[2], bbox[3]], [bbox[0], bbox[3]], [bbox[0], bbox[1]]]]
                },
                bbox=bbox,
                datetime=entry_time,
                properties={}
            )
            
            # Add assets from YAML (like original processing)
            for asset_config in assets_config:
                identifier = asset_config.get("Identifier", "data")
                file_url = asset_config.get("File")
                if file_url:
                    item.add_asset(
                        identifier,
                        Asset(
                            href=file_url,
                            media_type="image/tiff",
                            roles=["data"]
                        )
                    )
            
            # Store XYZ links for collection-level processing to avoid individual layers
            xyz_links_data = []
            for link_config in links_config:
                relation = link_config.get("Relation")
                url = link_config.get("URL")
                link_type = link_config.get("Type", "image/png")
                title = link_config.get("Title", "")
                
                if relation == "xyz" and url:
                    xyz_links_data.append({
                        "time": time_str,
                        "url": url,
                        "type": link_type,
                        "title": title
                    })
                    logging.info(f"Stored XYZ link for collection-level processing: {time_str}")
            
            # Store xyz links data for later processing
            if not hasattr(collection, '_xyz_links_data'):
                collection._xyz_links_data = []
            collection._xyz_links_data.extend(xyz_links_data)
            
            # Add the item to the collection
            collection.add_item(item)
            logging.info(f"Created STAC item for time: {time_str}")
            
        except ValueError as e:
            logging.error(f"Error parsing time {time_str}: {e}")
            continue
    
    # Update collection extents with actual data (like original processing)
    if min_time and max_time:
        # Update temporal extent
        collection.extent.temporal.intervals = [[min_time, max_time]]
        # Update spatial extent  
        collection.extent.spatial.bboxes = [bbox]
        logging.info(f"Set temporal extent: {min_time} to {max_time}")
        logging.info(f"Set spatial extent: {bbox}")
        
        # Add time series metadata to help EODash recognize this as a time series
        times = [time_entry.get("Time") for time_entry in time_entries if time_entry.get("Time")]
        if len(times) > 1:
            # Add EODash time series indicators
            collection.extra_fields["time_series"] = [{"time": t} for t in times]
            # Mark this as a time series collection
            collection.extra_fields["collection_type"] = "timeseries"
            logging.info(f"Added time series metadata with {len(times)} time points")
            
        # Add collection-level XYZ links for time series
        if hasattr(collection, '_xyz_links_data'):
            for xyz_data in collection._xyz_links_data:
                collection.add_link(
                    Link(
                        rel="xyz",
                        target=xyz_data["url"],
                        media_type=xyz_data["type"],
                        title=xyz_data["title"],
                        extra_fields={
                            "time": xyz_data["time"],
                            "role": ["data"]
                        }
                    )
                )
                logging.info(f"Added collection-level XYZ link for {xyz_data['time']}")
            
            # Clean up temp data
            delattr(collection, '_xyz_links_data')
    
    # Now the key part: Update the collection links to match original processing
    # The original processing adds datetime and assets to the collection item links
    items = list(collection.get_items())
    for item in items:
        # Find existing item link and enhance it with datetime and assets
        for link in collection.links:
            if (link.rel == "item" and 
                link.target and item.id in str(link.target)):
                
                # Add datetime and assets to the link (like original processing)
                link.extra_fields["datetime"] = item.datetime.isoformat().replace('+00:00', 'Z')
                
                # Add assets list to the link
                asset_urls = []
                for asset_key, asset in item.assets.items():
                    if asset_key != "data":  # Only include original assets, not generated ones
                        asset_urls.append(asset.href)
                
                if asset_urls:
                    link.extra_fields["assets"] = asset_urls
                
                logging.info(f"Enhanced collection link for item {item.id}")
    
    return collection
