"""
Pfander_watershed.py
Created: 2026-05-22
Author: Isabelle Pfander

Purpose:
    Delineate a watershed from a DEM and an outflow point using ArcPy.
    Workflow:
        - Fill sinks in DEM
        - Compute flow direction and accumulation
        - Snap pour point
        - Delineate watershed
        - Convert to polygon and compute area
"""

# --- Environment setup ---
import arcpy

# Set workspace and allow overwriting outputs
arcpy.env.workspace = (
    r"ENTER PATH HERE"
)
arcpy.env.overwriteOutput = True

# Input datasets
inRaster = "ENTER INPUT RASTER HERE"
damPoint = "ENTER INPUT POINT HERE"
outputPoly = "watershedPolygon"

# Explicit intermediate outputs to avoid ArcGIS auto‑generated names
filledDEM = "filledDEM"
flowDir = "flowDir"
flowAcc = "flowAcc"
snapPour = "snapPour"
watershedRaster = "watershedRaster"

# Helper function to print spatial reference system of inputs
def print_srs(dataset):
    try:
        srs = arcpy.Describe(dataset).spatialReference.name
        print(f"SRS of {dataset}: {srs}")
    except Exception as e:
        print(f"Could not read SRS for {dataset}: {e}")


# --- Hydrology processing ---
try:
    # Ensure Spatial Analyst tools are available
    arcpy.CheckOutExtension("Spatial")

    # Report SRS for input datasets
    print_srs(inRaster)
    print_srs(damPoint)

    # Fill sinks in DEM
    arcpy.sa.Fill(inRaster).save(filledDEM)

    # Generate flow direction raster
    arcpy.sa.FlowDirection(filledDEM).save(flowDir)

    # Compute flow accumulation from flow direction
    arcpy.sa.FlowAccumulation(flowDir).save(flowAcc)

    # Snap pour point to highest accumulation cell within 100 m
    arcpy.sa.SnapPourPoint(damPoint, flowAcc, 100).save(snapPour)

    # Delineate watershed draining to the snapped pour point
    arcpy.sa.Watershed(flowDir, snapPour).save(watershedRaster)

    # Convert watershed raster to polygon for area calculation
    arcpy.conversion.RasterToPolygon(watershedRaster, outputPoly, "NO_SIMPLIFY")

    # Add area field in square meters
    arcpy.management.CalculateGeometryAttributes(
        outputPoly,
        [["Area_m", "AREA"]],
        area_unit="SQUARE_METERS"
    )

except Exception as e:
    print("Processing error:", e)


# --- Area calculation ---
try:
    # Sum area values
    total_area = sum(row[0] for row in arcpy.da.SearchCursor(outputPoly, ["Area_m"]))

    # Print area in common hydrology units
    print(f"Total watershed area: {total_area:,.2f} m²")
    print(f"Area in hectares: {total_area / 10_000:,.2f} ha")
    print(f"Area in square kilometers: {total_area / 1_000_000:,.2f} km²")

except Exception as e:
    print("Error calculating total area:", e)
