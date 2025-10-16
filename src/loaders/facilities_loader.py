import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

class FacilitiesLoader:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def load(self) -> gpd.GeoDataFrame:
        df = pd.read_csv(self.csv_path, encoding='latin-1')

        # Check required columns
        if "Latitude" not in df.columns or "Longitude" not in df.columns:
            raise ValueError("CSV must contain 'Latitude' and 'Longitude' columns.")

        # Drop rows without coordinates
        df = df.dropna(subset=["Latitude", "Longitude"])

        # Create geometry column from lat/lon
        geometry = [Point(xy) for xy in zip(df["Longitude"], df["Latitude"])]

        # Create GeoDataFrame with WGS84 (EPSG:4326)
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        return gdf
