from pathlib import Path
from typing import Optional

class VectorProcessor(BaseProcessor):
    """Process vector (shapefile, geojson) data"""
    
    def load_shapefile(self, shapefile_path: str) -> gpd.GeoDataFrame:
        """Load shapefile"""
        self.logger.info(f"Loading shapefile: {shapefile_path}")
        return gpd.read_file(shapefile_path)
    
    def load_geojson(self, geojson_path: str) -> gpd.GeoDataFrame:
        """Load GeoJSON"""
        self.logger.info(f"Loading GeoJSON: {geojson_path}")
        return gpd.read_file(geojson_path)
    
    def filter_by_country(
        self,
        gdf: gpd.GeoDataFrame,
        country_code: str,
        code_column: str = 'ADM0_A3'
    ) -> gpd.GeoDataFrame:
        """Filter geodataframe by country code"""
        self.logger.info(f"Filtering data for country: {country_code}")
        filtered = gdf[gdf[code_column] == country_code].copy()
        self.logger.info(f"Retained {len(filtered)} records")
        return filtered
    
    def reproject(self, gdf: gpd.GeoDataFrame, crs: int) -> gpd.GeoDataFrame:
        """Reproject to target CRS"""
        self.logger.info(f"Reprojecting to EPSG:{crs}")
        if gdf.crs is None:
            gdf.set_crs(self.config['crs_wgs84'], inplace=True)
        return gdf.to_crs(epsg=crs)
    
    def remove_empty_geometry(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Remove features with empty geometry"""
        before = len(gdf)
        gdf = gdf[~gdf.geometry.is_empty].copy()
        removed = before - len(gdf)
        self.logger.info(f"Removed {removed} features with empty geometry")
        return gdf
    
    def clip_to_bounds(
        self,
        gdf: gpd.GeoDataFrame,
        bounds: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Clip data to boundary"""
        self.logger.info("Clipping data to boundaries")
        clipped = gpd.clip(gdf, bounds)
        self.logger.info(f"Retained {len(clipped)} features after clipping")
        return clipped
    
    def process(self, data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Default processing pipeline"""
        return data