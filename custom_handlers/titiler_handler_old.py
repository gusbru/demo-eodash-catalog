from pystac import Collection, Link, Item, Asset
from pystac.extensions.projection import ProjectionExtension
from pystac import SpatialExtent, TemporalExtent, Extent
from datetime import datetime
import urllib.parse

def process(collection, catalog_config, endpoint_config, collection_config):
    """Custom handler for titiler endpoints"""
    
    # Build the S3 URL
    s3_url = f"s3://{endpoint_config['S3Bucket']}/{endpoint_config['S3Key']}"
    base_url = endpoint_config["EndPoint"]
    encoded_s3_url = urllib.parse.quote(s3_url, safe='')
    
    # Build parameters for titiler
    params = []
    params.append(f"url={encoded_s3_url}")
    
    if endpoint_config.get("Bands"):
        for band in endpoint_config["Bands"]:
            params.append(f"bidx={band}")
    
    if endpoint_config.get("Rescale"):
        rescale_str = f"{endpoint_config['Rescale'][0]}%2C{endpoint_config['Rescale'][1]}"
        for _ in endpoint_config.get("Bands", [1]):
            params.append(f"rescale={rescale_str}")
    
    if endpoint_config.get("Reproject"):
        params.append(f"reproject={endpoint_config['Reproject']}")
    
    params_str = '&'.join(params)
    
    # Create titiler URLs
    tile_url = f"{base_url}/cog/tiles/{{z}}/{{x}}/{{y}}.png?{params_str}"
    info_url = f"{base_url}/cog/info?{params_str}"
    preview_url = f"{base_url}/cog/preview?{params_str}"
    thumbnail_url = f"{base_url}/cog/preview.png?{params_str}&max_size=512"
    
    # Create a STAC item with proper metadata
    datetime_str = endpoint_config.get("DateTime", "2020-10-30T18:21:38Z")
    item_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    
    # Define the bounding box
    bbox = endpoint_config.get("Bbox", [-114.0, 32.0, -113.0, 33.0])
    
    # Create geometry from bbox
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [bbox[0], bbox[1]],  # min_lon, min_lat
            [bbox[2], bbox[1]],  # max_lon, min_lat
            [bbox[2], bbox[3]],  # max_lon, max_lat
            [bbox[0], bbox[3]],  # min_lon, max_lat
            [bbox[0], bbox[1]]   # close polygon
        ]]
    }
    
    # Create the STAC item
    item = Item(
        id=f"venus-{item_datetime.strftime('%Y%m%d-%H%M%S')}",
        bbox=bbox,
        datetime=item_datetime,
        properties={
            "proj:epsg": 4326,
        },
        geometry=geometry
    )
    
    # CRITICAL: Add XYZ link for tiles (this is what EODash uses for rendering)
    item.add_link(Link(
        rel="xyz",
        target=tile_url,
        media_type="image/png",
        title="Titiler tiles",
        extra_fields={
            "roles": ["data", "visual"],  # Important: roles for links go in extra_fields
            "proj:epsg": 4326
        }
    ))
    
    # IMPORTANT: Also add a data asset to ensure isSupported = true
    # This provides a fallback and additional metadata
    item.add_asset(
        "tiles",
        Asset(
            href=tile_url,
            media_type="image/png",
            roles=["data", "visual"],  # CRITICAL: Must include "data" role
            extra_fields={
                "proj:epsg": 4326,
                "titiler:endpoint": "tiles"
            }
        )
    )
    
    # Add other assets
    item.add_asset(
        "preview",
        Asset(
            href=preview_url,
            media_type="image/png",
            roles=["overview"],
            extra_fields={
                "titiler:endpoint": "preview"
            }
        )
    )
    
    item.add_asset(
        "thumbnail",
        Asset(
            href=thumbnail_url,
            media_type="image/png",
            roles=["thumbnail"],
            extra_fields={
                "titiler:endpoint": "thumbnail"
            }
        )
    )
    
    item.add_asset(
        "info",
        Asset(
            href=info_url,
            media_type="application/json",
            roles=["metadata"],
            extra_fields={
                "titiler:endpoint": "info"
            }
        )
    )
    
    # Add the raw S3 URL if requested
    if endpoint_config.get("IncludeRawS3", False):
        item.add_asset(
            "raw_cog",
            Asset(
                href=s3_url,
                media_type="image/tiff",
                roles=["source"],  # Note: not "data" to avoid conflicts
                extra_fields={
                    "description": "Raw COG file in S3"
                }
            )
        )
    
    # Add the item to the collection
    collection.add_item(item)
    
    # Update the collection's spatial and temporal extent
    collection.extent.spatial = SpatialExtent([bbox])
    collection.extent.temporal = TemporalExtent([[item_datetime, item_datetime]])
    
    # Also add XYZ link to the collection level for compatibility
    collection.add_link(Link(
        rel="xyz",
        target=tile_url,
        media_type="image/png",
        title="Titiler tiles",
        extra_fields={
            "roles": ["data"],
            "proj:epsg": 4326
        }
    ))
    
    return collection