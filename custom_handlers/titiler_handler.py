from pystac import Collection, Link, Item, Asset
from pystac import SpatialExtent, TemporalExtent
from datetime import datetime
import urllib.parse

def process(collection, catalog_config, endpoint_config, collection_config):
    """Custom handler with direct link manipulation"""
    
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
    
    # Create titiler tile URL
    tile_url = f"{base_url}/cog/tiles/{{z}}/{{x}}/{{y}}.png?{params_str}"
    
    print(f"=== TITILER HANDLER DEBUG ===")
    print(f"Generated tile URL: {tile_url}")
    
    # Create other URLs
    info_url = f"{base_url}/cog/info?{params_str}"
    preview_url = f"{base_url}/cog/preview?{params_str}"
    thumbnail_url = f"{base_url}/cog/preview.png?{params_str}&max_size=512"
    
    # Create a STAC item
    datetime_str = endpoint_config.get("DateTime", "2020-10-30T18:21:38Z")
    item_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    bbox = endpoint_config.get("Bbox", [-114.0, 32.0, -113.0, 33.0])
    
    item = Item(
        id=item_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'),
        bbox=bbox,
        datetime=item_datetime,
        properties={
            "proj:epsg": 4326,
        },
        geometry={
            "type": "Polygon",
            "coordinates": [[[bbox[0], bbox[1]], [bbox[2], bbox[1]], 
                           [bbox[2], bbox[3]], [bbox[0], bbox[3]], [bbox[0], bbox[1]]]]
        }
    )
    
    # SOLUTION: Create a custom link object that behaves like PySTAC but has href
    class CustomLink:
        def __init__(self, rel, href, media_type, title, **extra_fields):
            self.rel = rel
            self.href = href  # This is the key - direct href property
            self.target = href  # Also set target for PySTAC compatibility
            self.media_type = media_type
            self.type = media_type  # Some systems expect 'type' instead of 'media_type'
            self.title = title
            
            # Add extra fields as attributes
            for key, value in extra_fields.items():
                setattr(self, key, value)
        
        def to_dict(self, **kwargs):
            """Convert to dictionary format expected by PySTAC"""
            result = {
                "rel": self.rel,
                "href": self.href,
                "type": self.media_type,
                "title": self.title
            }
            # Add any extra fields that were set
            for key, value in self.__dict__.items():
                if key not in ["rel", "href", "media_type", "type", "title", "target"]:
                    result[key] = value
            return result
        
        def is_hierarchical(self):
            """Return whether this link is hierarchical (used by PySTAC)"""
            return False
    
    # Create XYZ link with direct href access
    xyz_link = CustomLink(
        rel="xyz",
        href=tile_url,
        media_type="image/png",
        title="Titiler XYZ Tiles"
    )
    
    print(f"Custom Link rel: {xyz_link.rel}")
    print(f"Custom Link href: {xyz_link.href}")
    print(f"Custom Link media_type: {xyz_link.media_type}")
    
    # Add the custom link to the item
    if not hasattr(item, 'links'):
        item.links = []
    
    item.links.append(xyz_link)
    
    # Add data asset to pass the isSupported check
    item.add_asset(
        "data",
        Asset(
            href=tile_url,
            media_type="image/png",
            roles=["data"],
            extra_fields={
                "proj:epsg": 3857
            }
        )
    )
    
    # Add other assets
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
    
    # Add to collection
    collection.add_item(item)
    collection.extent.spatial = SpatialExtent([bbox])
    collection.extent.temporal = TemporalExtent([[item_datetime, item_datetime]])
    
    print(f"Item has {len(item.links)} links")
    print(f"Item has {len(item.assets)} assets")
    
    # Debug final structure
    print("=== FINAL LINK STRUCTURE ===")
    for link in item.links:
        if hasattr(link, 'rel') and link.rel == "xyz":
            print(f"XYZ Link found:")
            print(f"  - rel: {link.rel}")
            print(f"  - href: {getattr(link, 'href', 'NOT SET')}")
            print(f"  - media_type: {getattr(link, 'media_type', 'NOT SET')}")
            print(f"  - title: {getattr(link, 'title', 'NOT SET')}")
    
    return collection