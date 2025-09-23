from pystac import Collection, Link
import logging

def handle_titiler_endpoint(
    collection: Collection,
    catalog_config: dict,
    endpoint_config: dict,
    collection_config: dict
) -> Collection:
    """Custom TiTiler endpoint handler"""
    
    # Generate TiTiler URL template
    titiler_base = endpoint_config["EndPoint"]
    cog_url_template = endpoint_config.get("COG_URL", "{cog_url}")
    
    # Build the basic TiTiler URL
    target_url = f"{titiler_base}/cog/tiles/{{z}}/{{x}}/{{y}}"
    
    # Add query parameters
    params = []
    params.append(f"url={cog_url_template}")
    
    if endpoint_config.get("Rescale"):
        vmin, vmax = endpoint_config["Rescale"]
        params.append(f"rescale={vmin},{vmax}")
    
    if endpoint_config.get("Colormap"):
        params.append(f"colormap_name={endpoint_config['Colormap']}")
    
    # Add other common TiTiler parameters
    if endpoint_config.get("Assets"):
        assets = ",".join(endpoint_config["Assets"])
        params.append(f"assets={assets}")
    
    if endpoint_config.get("Expression"):
        params.append(f"expression={endpoint_config['Expression']}")
    
    if endpoint_config.get("NoData") is not None:
        params.append(f"nodata={endpoint_config['NoData']}")
    
    # Combine URL with parameters
    if params:
        target_url += "?" + "&".join(params)
    
    # Add extra fields for EODash
    extra_fields = {
        "role": ["data"],
    }
    
    # Add projection info if specified
    if endpoint_config.get("DataProjection"):
        extra_fields["proj:epsg"] = endpoint_config["DataProjection"]
    
    # Add link to collection
    collection.add_link(
        Link(
            rel="xyz",
            target=target_url,
            media_type="image/png",
            title=f"TiTiler tiles - {collection_config['Title']}",
            extra_fields=extra_fields
        )
    )
    
    logging.info(f"Added TiTiler link: {target_url}")
    return collection