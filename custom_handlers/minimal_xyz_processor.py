import logging
from datetime import datetime

from pystac import Link


def process(
    collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
):
    """Minimal processor that only adds XYZ links to existing items without changing structure"""
    
    time_entries = endpoint_config.get("TimeEntries", [])
    
    if not time_entries:
        logging.warning("No TimeEntries found in endpoint_config")
        return collection
    
    # Process existing items and add XYZ links
    for item in collection.get_items():
        item_time = item.datetime
        if not item_time:
            continue
            
        # Find matching time entry
        for time_entry in time_entries:
            time_str = time_entry.get("Time")
            if time_str:
                try:
                    entry_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if item_time == entry_time:
                        # Found matching time entry, add XYZ links from YAML
                        links_config = time_entry.get("Links", [])
                        for link_config in links_config:
                            relation = link_config.get("Relation")
                            url = link_config.get("URL")
                            link_type = link_config.get("Type", "image/png")
                            title = link_config.get("Title", "")
                            
                            if relation == "xyz" and url:
                                item.add_link(
                                    Link(
                                        rel="xyz",
                                        target=url,
                                        media_type=link_type,
                                        title=title
                                    )
                                )
                                logging.info(f"Added XYZ link to existing item {item.id}")
                        break
                except ValueError:
                    continue
    
    return collection
