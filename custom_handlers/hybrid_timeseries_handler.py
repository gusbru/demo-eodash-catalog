import logging
from datetime import datetime

from pystac import Asset, Collection, Item, Link


def process(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Hybrid handler that preserves original time series structure but adds XYZ links"""
    
    time_entries = endpoint_config.get("TimeEntries", [])
    
    if not time_entries:
        logging.warning("No TimeEntries found in endpoint_config")
        return collection
    
    # Process items that were already created by the standard YAML processor
    for item in collection.get_items():
        item_time = item.datetime
        if not item_time:
            continue
            
        # Find the matching time entry from YAML
        matching_entry = None
        for time_entry in time_entries:
            time_str = time_entry.get("Time")
            if time_str:
                try:
                    entry_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if item_time == entry_time:
                        matching_entry = time_entry
                        break
                except ValueError:
                    continue
        
        if not matching_entry:
            continue
            
        # Process Links from YAML and add them to the STAC item
        links = matching_entry.get("Links", [])
        for link_config in links:
            relation = link_config.get("Relation")
            url = link_config.get("URL")
            link_type = link_config.get("Type", "image/png")
            title = link_config.get("Title", "")
            
            if relation == "xyz" and url:
                # Add XYZ link to the item (this is what was missing!)
                item.add_link(
                    Link(
                        rel="xyz",
                        target=url,
                        media_type=link_type,
                        title=title
                    )
                )
                logging.info(f"Added XYZ link to item {item.id}: {url}")
    
    logging.info(f"Processed {len(list(collection.get_items()))} items with XYZ links")
    return collection
