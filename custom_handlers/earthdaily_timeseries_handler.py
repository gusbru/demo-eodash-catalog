import logging
import urllib.parse
from datetime import datetime

from pystac import Asset, Collection, Item, Link


def process(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Custom handler for EarthDaily time series data with TiTiler endpoints"""
    
    titiler_base = endpoint_config["EndPoint"]
    s3_bucket = endpoint_config["S3Bucket"]
    bands = endpoint_config.get("Bands", [1, 2, 3])
    rescale = endpoint_config.get("Rescale", [-50, 350])
    reproject = endpoint_config.get("Reproject", "bilinear")
    bbox = endpoint_config.get("Bbox")
    
    # Process each time entry
    for time_entry in endpoint_config.get("TimeEntries", []):
        time_str = time_entry["Time"]
        s3_key = time_entry["S3Key"]
        
        # Create S3 URL
        s3_url = f"s3://{s3_bucket}/{s3_key}"
        
        # Create TiTiler URL with URL encoding like titiler_handler.py
        titiler_url = f"{titiler_base}/cog/tiles/{{z}}/{{x}}/{{y}}.png"
        encoded_s3_url = urllib.parse.quote(s3_url, safe='')
        
        # Build query parameters in same order as titiler_handler.py
        params = [
            f"url={encoded_s3_url}"
        ]
        
        # Add band indices first
        for band in bands:
            params.append(f"bidx={band}")
        
        # Add rescale parameters (one per band)
        rescale_str = f"{rescale[0]}%2C{rescale[1]}"
        for _ in bands:
            params.append(f"rescale={rescale_str}")
        
        # Add reproject
        if reproject:
            params.append(f"reproject={reproject}")
        
        full_url = f"{titiler_url}?{'&'.join(params)}"
        
        # Parse datetime
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        # Create STAC Item for this time entry
        item_id = f"{collection_config['Name']}_{dt.strftime('%Y%m%d_%H%M%S')}"
        
        item = Item(
            id=item_id,
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
        
        # Add RGB composite asset
        item.add_asset(
            "rgb_composite",
            Asset(
                href=s3_url,
                media_type="image/tiff",
                title="RGB Composite",
                roles=["data"]
            )
        )
        
        # Add additional assets like titiler_handler.py
        # Create other URLs
        info_url = f"{titiler_base}/cog/info?{'&'.join(params[1:])}&url={encoded_s3_url}"
        preview_url = f"{titiler_base}/cog/preview?{'&'.join(params[1:])}&url={encoded_s3_url}"
        thumbnail_url = f"{titiler_base}/cog/preview.png?{'&'.join(params[1:])}&url={encoded_s3_url}&max_size=512"
        
        item.add_asset(
            "data",
            Asset(
                href=full_url,
                media_type="image/png",
                roles=["data"],
                extra_fields={
                    "proj:epsg": 3857
                }
            )
        )
        
        item.add_asset(
            "info",
            Asset(
                href=info_url,
                media_type="application/json",
                roles=["metadata"]
            )
        )
        
        item.add_asset(
            "preview",
            Asset(
                href=preview_url,
                media_type="image/png",
                roles=["overview"]
            )
        )
        
        item.add_asset(
            "thumbnail",
            Asset(
                href=thumbnail_url,
                media_type="image/png",
                roles=["thumbnail"]
            )
        )
        
        # Add TiTiler XYZ link
        item.add_link(
            Link(
                rel="xyz",
                target=full_url,
                media_type="image/png",
                title="TiTiler RGB tiles",
                extra_fields={
                    "role": ["data"],
                    "proj:epsg": 4326
                }
            )
        )
        
        # Add item to collection
        collection.add_item(item)
        
        logging.info(f"Added time series item: {item_id} with TiTiler URL: {full_url}")
    
    return collection
