import logging
from datetime import datetime

from pystac import Asset, Collection, Link


def process(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Custom handler that creates collection-level time series without separate items"""
    
    # Extract parameters
    bbox = endpoint_config.get("Bbox", [-115.2, 32.0, -114.0, 33.2])
    time_entries = endpoint_config.get("TimeEntries", [])
    
    if not time_entries:
        logging.warning("No TimeEntries found in endpoint_config")
        return collection
    
    # Add time series data as collection-level links and properties
    time_data = []
    
    for time_entry in time_entries:
        time_str = time_entry.get("Time")
        links = time_entry.get("Links", [])
        
        if not time_str:
            continue
            
        # Find XYZ link for this time entry
        for link_config in links:
            relation = link_config.get("Relation")
            url = link_config.get("URL")
            
            if relation == "xyz" and url:
                # Add collection-level link with time information
                collection.add_link(
                    Link(
                        rel="xyz",
                        target=url,
                        media_type="image/png",
                        title=f"TiTiler tiles for {time_str}",
                        extra_fields={
                            "time": time_str,
                            "role": ["data"],
                            "proj:epsg": 4326
                        }
                    )
                )
                
                time_data.append({
                    "time": time_str,
                    "url": url
                })
                
                logging.info(f"Added collection-level XYZ link for {time_str}")
    
    # Add time series metadata to collection
    if time_data:
        collection.extra_fields["time_series"] = time_data
        
        # Set temporal extent
        times = [datetime.fromisoformat(t["time"].replace('Z', '+00:00')) for t in time_data]
        min_time = min(times)
        max_time = max(times)
        
        collection.extent.temporal.intervals = [[min_time, max_time]]
        collection.extent.spatial.bboxes = [bbox]
    
    return collection
