from pystac import Collection, Item, Asset, Link
from datetime import datetime
import logging

def execute(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """EarthDaily TiTiler endpoint handler that creates items with assets"""
    
    # Define your time entries and corresponding files
    time_entries = [
        {
            "datetime": "2020-10-30T18:21:38Z",
            "file": "s3://earthdaily-prod-marketing-platform/aircraftdetection/YUMA-2-v1-2023-02-11/20201030-182138/VENUS-XS_20201030-182138-000_L2A_YUMA-2_C_V2-2_SRE_RGB.tif"
        },
        {
            "datetime": "2020-11-15T18:21:38Z", 
            "file": "s3://earthdaily-prod-marketing-platform/aircraftdetection/YUMA-2-v1-2023-02-11/20201115-182138/VENUS-XS_20201115-182138-000_L2A_YUMA-2_C_V2-2_SRE_RGB.tif"
        }
    ]
    
    # Create items for each time entry
    for entry in time_entries:
        dt = datetime.fromisoformat(entry["datetime"].replace('Z', '+00:00'))
        
        # Create asset pointing to the COG file
        asset = Asset(
            href=entry["file"],
            media_type="image/tiff",
            roles=["data"],
            extra_fields={
                "titiler:endpoint": endpoint_config["EndPoint"],
                "titiler:params": {
                    "bidx": [1, 2, 3],
                    "rescale": [[-50, 350], [-50, 350], [-50, 350]],
                    "reproject": "bilinear"
                }
            }
        )
        
        # Create STAC item
        item = Item(
            id=dt.strftime("%Y%m%dT%H%M%S"),
            bbox=endpoint_config.get("Bbox", [-114.8, 32.4, -114.4, 32.8]),
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [-114.8, 32.4], [-114.4, 32.4], 
                    [-114.4, 32.8], [-114.8, 32.8], 
                    [-114.8, 32.4]
                ]]
            },
            datetime=dt,
            properties={},
            assets={"cog": asset}
        )
        
        # Add TiTiler link to the item
        titiler_url = f"{endpoint_config['EndPoint']}/cog/tiles/{{z}}/{{x}}/{{y}}.png?url={entry['file']}&bidx=1&bidx=2&bidx=3&rescale=-50%2C350&rescale=-50%2C350&rescale=-50%2C350&reproject=bilinear"
        
        item.add_link(Link(
            rel="xyz",
            target=titiler_url,
            media_type="image/png",
            title="TiTiler RGB tiles"
        ))
        
        # Add item to collection
        collection.add_item(item)
    
    logging.info(f"Added {len(time_entries)} items to collection")
    return collection