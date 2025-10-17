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

            populations = []
            for idx, row in gdf.iterrows():
                try:
                    stat = zonal_stats(
                        [row.geometry],
                        self.raster_path,
                        stats=['sum'],
                        nodata=src.nodata,
                        all_touched=False,
                    )
                    pop = stat[0]['sum'] if stat[0]['sum'] is not None else 0
                except Exception as e:
                    print(f"Warning: Failed to process geometry {idx}: {e}")
                    pop = 0
                populations.append(pop)
            gdf['population'] = populations

        # Attach stats to the GeoDataFrame
        #gdf["pop_sum"] = [s["sum"] for s in stats]
        #gdf["pop_mean"] = [s["mean"] for s in stats]

        # Add stats to GeoDataFrame
        #gdf['population'] = [s['sum'] if s['sum'] is not None else 0 for s in stats]
        #gdf['pop_mean'] = [s['mean'] if s['mean'] is not None else 0 for s in stats]

        # Save to GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")
        return gdf
