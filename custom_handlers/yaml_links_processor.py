import logging
from datetime import datetime

from pystac import Asset, Collection, Item, Link


def process(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Handler that creates proper time series items from YAML TimeEntries with XYZ links"""
    
    time_entries = endpoint_config.get("TimeEntries", [])
    bbox = endpoint_config.get("Bbox", [-180, -90, 180, 90])
    
    if not time_entries:
        logging.warning("No TimeEntries found in endpoint_config")
        return collection
    
    # Clear any existing items (in case they were improperly created)
    collection.clear_items()
    
    # Track min/max times for temporal extent
    min_time = None
    max_time = None
    
    # Create proper STAC items for each time entry
    for time_entry in time_entries:
        time_str = time_entry.get("Time")
        assets = time_entry.get("Assets", [])
        links = time_entry.get("Links", [])
        
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
            
            # Create STAC item
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
            
            # Add assets from YAML
            for asset_config in assets:
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
            
            # Add links from YAML (this is the key part!)
            for link_config in links:
                relation = link_config.get("Relation")
                url = link_config.get("URL")
                link_type = link_config.get("Type", "image/png")
                title = link_config.get("Title", "")
                
                if relation == "xyz" and url:
                    # Add XYZ link to the item
                    item.add_link(
                        Link(
                            rel="xyz",
                            target=url,
                            media_type=link_type,
                            title=title
                        )
                    )
                    logging.info(f"Added XYZ link to item {item.id}: {url}")
            
            # Add the item to the collection
            collection.add_item(item)
            logging.info(f"Created STAC item for time: {time_str}")
            
        except ValueError as e:
            logging.error(f"Error parsing time {time_str}: {e}")
            continue
    
    # Update collection temporal extent with actual data times  
    if min_time and max_time:
        # Update the temporal extent with datetime objects
        collection.extent.temporal.intervals = [[min_time, max_time]]
        # Also fix the spatial extent to use the actual bbox from config
        collection.extent.spatial.bboxes = [bbox]
        logging.info(f"Set temporal extent: {min_time} to {max_time}")
        logging.info(f"Set spatial extent: {bbox}")
        
        # Add timeseries extension metadata to help EODash recognize it as a time series
        # Based on STAC timeseries extension patterns AND EODash-specific patterns
        times = [time_entry.get("Time") for time_entry in time_entries if time_entry.get("Time")]
        if len(times) > 1:  # Only if we have multiple time points
            # Standard STAC timeseries extension
            collection.extra_fields["ts:dates"] = times
            collection.extra_fields["stac_extensions"] = [
                "https://stac-extensions.github.io/timeseries/v1.0.0/schema.json"
            ]
            
            # EODash-specific time_series field (seen in timeseries_collection_handler.py)
            time_series_data = []
            for time_entry in time_entries:
                time_str = time_entry.get("Time")
                if time_str:
                    time_series_data.append({"time": time_str})
            
            collection.extra_fields["time_series"] = time_series_data
            logging.info(f"Added both STAC and EODash timeseries metadata with {len(times)} dates")
    
    return collection
