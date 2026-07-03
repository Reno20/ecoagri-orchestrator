"""
EcoAgri-Orchestrator — MCP Server (stdio transport)
====================================================

Domain-specific tools for the Sasthamcotta Lake eco-agri nexus.
Exposes 5 tools via the Model Context Protocol (MCP) using stdio transport.

Tools:
  1. query_water_quality     — Water quality metrics for Sasthamcotta zones
  2. lookup_watershed_zone   — Determine watershed zone from location
  3. get_crop_sustainability — Sustainability rating for a crop in the region
  4. get_market_prices       — Current commodity prices in Kollam district
  5. get_soil_erosion_data   — Soil erosion risk assessment by terrain type
"""

import json
import logging
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP(
    "ecoagri-mcp-server",
    instructions=(
        "Domain-specific tools for ecological and agricultural data "
        "in the Sasthamcotta Lake watershed, Kerala, India."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATED DATA STORES
# ═══════════════════════════════════════════════════════════════════════════════

WATER_QUALITY_DATA = {
    "buffer": {
        "zone": "Buffer Zone (0-500m from lake)",
        "ph": 6.8,
        "dissolved_oxygen_mg_l": 5.2,
        "turbidity_ntu": 18.5,
        "nitrate_mg_l": 12.3,
        "phosphate_mg_l": 0.8,
        "coliform_mpn": 450,
        "status": "DEGRADED",
        "primary_pollutants": ["agrochemical runoff", "organic waste", "silt deposits"],
        "last_updated": "2026-06-15",
    },
    "transition": {
        "zone": "Transition Zone (500m-2km)",
        "ph": 7.1,
        "dissolved_oxygen_mg_l": 6.1,
        "turbidity_ntu": 12.0,
        "nitrate_mg_l": 8.7,
        "phosphate_mg_l": 0.5,
        "coliform_mpn": 220,
        "status": "MODERATE",
        "primary_pollutants": ["fertilizer leaching", "pesticide traces"],
        "last_updated": "2026-06-15",
    },
    "outer": {
        "zone": "Outer Zone (2km+)",
        "ph": 7.3,
        "dissolved_oxygen_mg_l": 7.0,
        "turbidity_ntu": 6.2,
        "nitrate_mg_l": 4.1,
        "phosphate_mg_l": 0.2,
        "coliform_mpn": 80,
        "status": "ACCEPTABLE",
        "primary_pollutants": ["minor agricultural runoff"],
        "last_updated": "2026-06-15",
    },
}

CROP_SUSTAINABILITY = {
    "tapioca": {
        "crop": "Tapioca (Cassava)",
        "sustainability_score": 15,
        "erosion_impact": "CRITICAL",
        "water_pollution_risk": "HIGH",
        "reason": "Weakens soil structure, causes massive erosion and silt deposition into Sasthamcotta Lake",
        "recommended_alternative": "Banana (Nendran), Turmeric, Ginger",
        "transition_support": "KSPB subsidy available for crop transition",
    },
    "rubber": {
        "crop": "Rubber (Hevea brasiliensis)",
        "sustainability_score": 45,
        "erosion_impact": "MODERATE",
        "water_pollution_risk": "MODERATE",
        "reason": "Chemical processing waste (formic acid, ammonia) contaminates groundwater",
        "recommended_alternative": "Mixed agroforestry (rubber + pepper + cocoa)",
        "transition_support": "Rubber Board intercropping scheme available",
    },
    "cashew": {
        "crop": "Cashew (Anacardium occidentale)",
        "sustainability_score": 60,
        "erosion_impact": "LOW",
        "water_pollution_risk": "MODERATE",
        "reason": "Deep root system prevents erosion but agrochemical use requires monitoring",
        "recommended_alternative": "Organic cashew with cover crop understory",
        "transition_support": "INDOCERT organic certification pathway",
    },
    "coconut": {
        "crop": "Coconut (Cocos nucifera)",
        "sustainability_score": 70,
        "erosion_impact": "LOW",
        "water_pollution_risk": "LOW",
        "reason": "Traditional Kerala crop with established sustainable practices",
        "recommended_alternative": "Integrated coconut + intercrop (banana, pineapple)",
        "transition_support": "KERAFED procurement guaranteed",
    },
    "rice": {
        "crop": "Rice (Pokkali / Kuttanad varieties)",
        "sustainability_score": 90,
        "erosion_impact": "NEGLIGIBLE",
        "water_pollution_risk": "LOW",
        "reason": "Paddy fields act as natural water filtration and flood buffers",
        "recommended_alternative": "Already optimal — maintain organic practices",
        "transition_support": "MSP guaranteed by Government of Kerala",
    },
    "pepper": {
        "crop": "Black Pepper (Piper nigrum)",
        "sustainability_score": 80,
        "erosion_impact": "LOW",
        "water_pollution_risk": "LOW",
        "reason": "Vine crop grown on support trees, minimal ground disturbance",
        "recommended_alternative": "Already sustainable — pair with shade trees",
        "transition_support": "Spices Board India export facilitation",
    },
}

MARKET_PRICES = {
    "coconut": {"commodity": "Coconut", "unit": "per kg", "min_price": 25, "max_price": 35, "trend": "STABLE", "demand": "HIGH"},
    "cashew_raw": {"commodity": "Cashew (Raw)", "unit": "per kg", "min_price": 120, "max_price": 180, "trend": "RISING", "demand": "HIGH"},
    "rubber_rss4": {"commodity": "Rubber RSS4", "unit": "per kg", "min_price": 170, "max_price": 200, "trend": "STABLE", "demand": "MODERATE"},
    "banana_nendran": {"commodity": "Banana (Nendran)", "unit": "per kg", "min_price": 30, "max_price": 45, "trend": "RISING", "demand": "HIGH"},
    "tapioca": {"commodity": "Tapioca", "unit": "per kg", "min_price": 8, "max_price": 12, "trend": "DECLINING", "demand": "LOW"},
    "pepper": {"commodity": "Black Pepper", "unit": "per kg", "min_price": 400, "max_price": 550, "trend": "RISING", "demand": "VERY HIGH"},
    "turmeric": {"commodity": "Turmeric", "unit": "per kg", "min_price": 80, "max_price": 120, "trend": "RISING", "demand": "HIGH"},
    "ginger": {"commodity": "Ginger", "unit": "per kg", "min_price": 60, "max_price": 90, "trend": "STABLE", "demand": "MODERATE"},
}

EROSION_DATA = {
    "steep_slope": {"terrain": "Steep Slope (>15°)", "erosion_risk": "CRITICAL", "annual_soil_loss_tons_ha": 45.0, "mitigation": ["Terracing mandatory", "Contour bunding", "Vetiver grass barriers", "Check dams"]},
    "moderate_slope": {"terrain": "Moderate Slope (5-15°)", "erosion_risk": "HIGH", "annual_soil_loss_tons_ha": 22.0, "mitigation": ["Contour bunding", "Cover crops", "Mulching with coir pith"]},
    "gentle_slope": {"terrain": "Gentle Slope (2-5°)", "erosion_risk": "MODERATE", "annual_soil_loss_tons_ha": 8.0, "mitigation": ["Grass waterways", "Strip cropping", "Organic mulching"]},
    "flat": {"terrain": "Flat/Lowland (<2°)", "erosion_risk": "LOW", "annual_soil_loss_tons_ha": 2.0, "mitigation": ["Standard drainage management", "Paddy cultivation recommended"]},
    "riverbank": {"terrain": "Riverbank/Lakeside", "erosion_risk": "CRITICAL", "annual_soil_loss_tons_ha": 60.0, "mitigation": ["10m buffer strip mandatory", "Vetiver/lemongrass planting", "No tillage zone", "Riparian forest restoration"]},
}


# ═══════════════════════════════════════════════════════════════════════════════
# MCP TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def query_water_quality(zone: str) -> str:
    """Query water quality metrics for a Sasthamcotta Lake watershed zone.

    Args:
        zone: The watershed zone to query. One of: buffer, transition, outer.

    Returns:
        JSON string with water quality metrics including pH, dissolved oxygen,
        turbidity, nitrate levels, phosphate, coliform count, and pollution status.
    """
    zone_key = zone.lower().strip()
    if zone_key not in WATER_QUALITY_DATA:
        return json.dumps({
            "error": f"Unknown zone '{zone}'. Valid zones: buffer, transition, outer",
            "valid_zones": list(WATER_QUALITY_DATA.keys()),
        })
    data = WATER_QUALITY_DATA[zone_key].copy()
    data["query_timestamp"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(data, indent=2)


@mcp.tool()
def lookup_watershed_zone(location: str) -> str:
    """Determine the Sasthamcotta watershed zone for a given location in Kerala.

    Args:
        location: A location name or description near Sasthamcotta Lake,
                  e.g. 'Kunnathur', 'near the lake shore', 'Sasthamcotta town'.

    Returns:
        JSON string with the determined watershed zone, distance estimate,
        and applicable regulations.
    """
    loc = location.lower().strip()

    # Simple keyword-based zone determination
    buffer_keywords = ["shore", "lakeside", "bank", "waterfront", "adjacent", "kayal"]
    transition_keywords = ["kunnathur", "sasthamcotta", "near lake", "close to", "nearby", "west kallada"]
    outer_keywords = ["kollam", "punalur", "anchal", "chadayamangalam", "pathanapuram", "outer"]

    if any(kw in loc for kw in buffer_keywords):
        zone = "buffer"
        distance_km = "< 0.5 km"
        regulations = [
            "NO intensive agriculture permitted",
            "Only native vegetation and buffer plantings allowed",
            "Mandatory 50m no-build setback",
            "Zero chemical input zone",
        ]
    elif any(kw in loc for kw in transition_keywords):
        zone = "transition"
        distance_km = "0.5 - 2 km"
        regulations = [
            "Only approved low-impact crops (rice, coconut, spices)",
            "Organic farming mandatory",
            "Maximum 50% land under cultivation",
            "Buffer strips required along all waterways",
        ]
    elif any(kw in loc for kw in outer_keywords):
        zone = "outer"
        distance_km = "> 2 km"
        regulations = [
            "Standard agricultural regulations apply",
            "Integrated pest management recommended",
            "Agrochemical usage monitoring required",
            "Soil conservation practices encouraged",
        ]
    else:
        zone = "transition"
        distance_km = "estimated 0.5 - 2 km"
        regulations = [
            "Default classification — provide more specific location for accuracy",
            "Transition zone regulations apply as precaution",
        ]

    return json.dumps({
        "location_input": location,
        "determined_zone": zone,
        "estimated_distance_to_lake": distance_km,
        "applicable_regulations": regulations,
        "authority": "Kerala State Pollution Control Board (KSPCB)",
        "query_timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2)


@mcp.tool()
def get_crop_sustainability(crop_name: str) -> str:
    """Get the sustainability rating and ecological impact of a crop in the Sasthamcotta region.

    Args:
        crop_name: Name of the crop, e.g. 'tapioca', 'rubber', 'coconut', 'rice', 'pepper', 'cashew'.

    Returns:
        JSON string with sustainability score (0-100), erosion impact level,
        water pollution risk, recommended alternatives, and available support schemes.
    """
    crop_key = crop_name.lower().strip()

    # Try to match partial names
    matched = None
    for key in CROP_SUSTAINABILITY:
        if key in crop_key or crop_key in key:
            matched = key
            break

    if not matched:
        return json.dumps({
            "error": f"No data for crop '{crop_name}'.",
            "available_crops": list(CROP_SUSTAINABILITY.keys()),
            "suggestion": "Try one of the listed crops or a common Kerala crop name.",
        })

    data = CROP_SUSTAINABILITY[matched].copy()
    data["query_timestamp"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(data, indent=2)


@mcp.tool()
def get_market_prices(commodity: str) -> str:
    """Get current market prices for agricultural commodities in Kollam district.

    Args:
        commodity: Name of the commodity, e.g. 'coconut', 'cashew_raw', 'pepper', 'rubber_rss4', 'banana_nendran'.

    Returns:
        JSON string with current price range (INR), market trend,
        demand level, and the Kollam APMC reference.
    """
    commodity_key = commodity.lower().strip().replace(" ", "_")

    # Try to match partial names
    matched = None
    for key in MARKET_PRICES:
        if key in commodity_key or commodity_key in key:
            matched = key
            break

    if not matched:
        return json.dumps({
            "error": f"No price data for '{commodity}'.",
            "available_commodities": list(MARKET_PRICES.keys()),
            "suggestion": "Try one of the listed commodities.",
        })

    data = MARKET_PRICES[matched].copy()
    data["market"] = "Kollam APMC (Agricultural Produce Market Committee)"
    data["currency"] = "INR"
    data["price_date"] = "2026-06-30"
    data["query_timestamp"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(data, indent=2)


@mcp.tool()
def get_soil_erosion_data(terrain_type: str) -> str:
    """Get soil erosion risk assessment and mitigation strategies by terrain type.

    Args:
        terrain_type: Type of terrain. One of: steep_slope, moderate_slope, gentle_slope, flat, riverbank.

    Returns:
        JSON string with erosion risk level, estimated annual soil loss,
        and recommended mitigation measures for the Sasthamcotta watershed.
    """
    terrain_key = terrain_type.lower().strip().replace(" ", "_")

    # Try to match partial names
    matched = None
    for key in EROSION_DATA:
        if key in terrain_key or terrain_key in key:
            matched = key
            break

    if not matched:
        return json.dumps({
            "error": f"No erosion data for terrain '{terrain_type}'.",
            "available_terrains": list(EROSION_DATA.keys()),
            "suggestion": "Try one of the listed terrain types.",
        })

    data = EROSION_DATA[matched].copy()
    data["region"] = "Sasthamcotta Lake Watershed, Kerala"
    data["data_source"] = "Kerala Soil Survey & Conservation Dept"
    data["query_timestamp"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT (stdio transport)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run(transport="stdio")
