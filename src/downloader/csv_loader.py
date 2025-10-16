import pandas as pd
import geopandas as gpd
from src.downloader.base import BaseDownloader

class CSVDataLoader(BaseDownloader):
    """Load specialist or facility data from CSV files"""
    def __init__(self, output_dir: str, csv_path: str, lat_col: str = 'latitude', 
                 lon_col: str = 'longitude'):
        super().__init__(output_dir)
        self.csv_path = csv_path
        self.lat_col = lat_col
        self.lon_col = lon_col
    
    def load_csv_to_geodataframe(self) -> gpd.GeoDataFrame:
        """
        Load CSV with coordinates and convert to GeoDataFrame
        
        Expected CSV columns:
        - latitude/lat/y
        - longitude/lon/x
        - name (facility/specialist name)
        - type/category (optional)
        - specialty (optional, for specialists)
        """
        self.logger.info(f"Loading CSV data from {self.csv_path}...")
        
        try:
            #load CSV
            df = pd.read_csv(self.csv_path)
            self.logger.info(f"Loaded {len(df)} records from CSV")
            
            #Validating columns
            if self.lat_col not in df.columns or self.lon_col not in df.columns:
                raise ValueError(
                    f"CSV must contain '{self.lat_col}' and '{self.lon_col}' columns. "
                    f"Found: {df.columns.tolist()}"
                )
            
            # Remove rows with missing coordinates
            df = df.dropna(subset=[self.lat_col, self.lon_col])
            self.logger.info(f"Retained {len(df)} records with valid coordinates")
            
            #create GeoDataFrame
            from shapely.geometry import Point
            geometry = [Point(xy) for xy in zip(df[self.lon_col], df[self.lat_col])]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
            
            #saving as GeoJSON
            output_path = self.output_dir / "csv_data.geojson"
            gdf.to_file(output_path, driver='GeoJSON')
            self.logger.info(f"Saved GeoJSON to {output_path}")
            
            return gdf
        
        except Exception as e:
            self.logger.error(f"Failed to load CSV data: {e}")
            raise
    
    def download(self) -> str:
        """Load CSV and return path to GeoJSON"""
        gdf = self.load_csv_to_geodataframe()
        return str(self.output_dir / "csv_data.geojson")