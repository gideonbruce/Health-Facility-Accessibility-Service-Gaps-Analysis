import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

class PopulationZonalExtractor:
    def __init__(self, boundary_path: str, raster_path: str):
        self.boundary_path = boundary_path
        self.raster_path = raster_path

    def run(self, output_path: str):
        # Load boundaries
        gdf = gpd.read_file(self.boundary_path)

        # Open raster and match CRS
        with rasterio.open(self.raster_path) as src:
            if gdf.crs != src.crs:
                gdf = gdf.to_crs(src.crs)

            stats = zonal_stats(
                gdf,
                self.raster_path,
                stats=["sum", "mean"],
                nodata=src.nodata
            )

        # Attach stats to the GeoDataFrame
        gdf["pop_sum"] = [s["sum"] for s in stats]
        gdf["pop_mean"] = [s["mean"] for s in stats]

        # Save to GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")
        return gdf
