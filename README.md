HFASGA Pipeline 🗺️






A Python geospatial analysis and visualization pipeline for mapping facilities, boundaries, roads, and population metrics. Built with GeoPandas, Folium, and a modular pipeline architecture for reproducible spatial analysis.

Table of Contents

Features

Project Structure

Installation

Usage

Configuration

Example

Screenshots

Troubleshooting

License

Features

Load and preprocess geospatial data: facilities, boundaries, roads

Compute accessibility metrics for facilities

Generate interactive maps with Folium:

Choropleth maps of population or other metrics

Facility markers

Roads and boundary overlays

Modular, reproducible pipeline

Efficient handling of large GeoDataFrames

Project Structure
HFASGA/
├─ src/
│  ├─ pipeline.py         # Main pipeline orchestrator
│  ├─ visualization/
│  │  ├─ maps.py          # Folium visualization utilities
│  ├─ processing/
│  │  ├─ data_loader.py   # Load and preprocess GeoDataFrames
│  ├─ config.py           # Configuration settings
│  ├─ logger.py           # Logging utilities
├─ data/
│  ├─ boundaries/         # Boundary shapefiles or GeoJSON
│  ├─ facilities/         # Facility datasets
│  ├─ roads/              # Road networks
├─ output/                # Generated maps and analysis
├─ main.py                # Entry point
├─ requirements.txt       # Dependencies
└─ README.md

Installation

Clone the repository:


Create and activate a conda environment:

conda create -n hfasga python=3.11
conda activate hfasga


Install dependencies:

pip install -r requirements.txt

Configuration

Edit src/config.py to set paths to your data:

DATA_DIR = "data/"
FACILITIES_PATH = DATA_DIR + "facilities/facilities.geojson"
BOUNDARIES_PATH = DATA_DIR + "boundaries/boundaries.geojson"
ROADS_PATH = DATA_DIR + "roads/roads.geojson"


Optional: set metric columns or map styles in config.py.

Usage

Run the pipeline:

python main.py


Outputs:

Interactive maps saved in output/

CSV or GeoJSON summaries of accessibility metrics

Choropleth and marker layers

Handling Timestamps

Folium requires all columns to be JSON-serializable. Convert datetime columns to strings:

for col in population_gdf.columns:
    if pd.api.types.is_datetime64_any_dtype(population_gdf[col]):
        population_gdf[col] = population_gdf[col].astype(str)


Alternatively, drop unnecessary timestamp columns before visualization.

Example
from src.pipeline import Pipeline

pipeline = Pipeline()
pipeline.run()


Generates a population choropleth

Adds facilities markers

Overlays roads and boundaries

Screenshots

Population Choropleth Map


Facilities and Accessibility Markers


Replace screenshots/*.png with your actual map exports.

Troubleshooting

Timestamp not JSON serializable
→ Convert datetime columns to string before passing to Folium

File not found errors
→ Check paths in config.py

Large GeoDataFrame performance issues
→ Simplify geometries: gdf.simplify(tolerance=0.001)

License

MIT License © 2025