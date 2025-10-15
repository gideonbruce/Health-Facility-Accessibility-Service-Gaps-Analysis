import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.merge import merge
import numpy as np
import geopandas as gpd
from src.processor.base import BaseProcessor

class RasterProcessor(BaseProcessor):
    """Process raster (GeoTIFF, DEM, population) data"""
    
    def load_raster(self, raster_path: str) -> tuple:
        """Load raster data"""
        self.logger.info(f"Loading raster: {raster_path}")
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            transform = src.transform
            crs = src.crs
            bounds = src.bounds
        return data, transform, crs, bounds
    
    def clip_raster(
        self,
        raster_path: str,
        clip_bounds: gpd.GeoDataFrame,
        output_path: str
    ) -> str:
        """Clip raster to bounds"""
        self.logger.info("Clipping raster to boundaries")
        
        # Ensure clip_bounds is in same CRS
        with rasterio.open(raster_path) as src:
            if clip_bounds.crs != src.crs:
                clip_bounds = clip_bounds.to_crs(src.crs)
        
        shapes = [geom for geom in clip_bounds.geometry]
        
        with rasterio.open(raster_path) as src:
            clipped_data, clipped_transform = mask(
                src,
                shapes,
                crop=True,
                all_touched=True
            )
            
            self._save_raster(
                output_path,
                clipped_data,
                clipped_transform,
                src.crs,
                src.nodata
            )
        
        self.logger.info(f"Clipped raster saved to {output_path}")
        return output_path
    
    def reproject_raster(
        self,
        raster_path: str,
        output_path: str,
        target_crs: int
    ) -> str:
        """Reproject raster to target CRS"""
        self.logger.info(f"Reprojecting raster to EPSG:{target_crs}")
        
        with rasterio.open(raster_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs,
                f'EPSG:{target_crs}',
                src.width,
                src.height,
                *src.bounds
            )
            
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': f'EPSG:{target_crs}',
                'transform': transform,
                'width': width,
                'height': height
            })
            
            with rasterio.open(output_path, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=f'EPSG:{target_crs}',
                        resampling=Resampling.bilinear
                    )
        
        self.logger.info(f"Reprojected raster saved to {output_path}")
        return output_path
    
    def merge_rasters(
        self,
        raster_paths: list,
        output_path: str
    ) -> str:
        """Merge multiple raster files (e.g., DEM tiles)"""
        self.logger.info(f"Merging {len(raster_paths)} raster files")
        
        src_files_to_mosaic = []
        for path in raster_paths:
            src = rasterio.open(path)
            src_files_to_mosaic.append(src)
        
        mosaic, out_trans = merge(src_files_to_mosaic)
        
        # Get metadata from first file
        out_meta = src_files_to_mosaic[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
        })
        
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        # Close all source files
        for src in src_files_to_mosaic:
            src.close()
        
        self.logger.info(f"Merged raster saved to {output_path}")
        return output_path
    
    def extract_population_by_zones(
        self,
        population_raster_path: str,
        zones: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """
        Extract population statistics for each administrative zone
        (e.g., sum population per county)
        """
        self.logger.info("Extracting population by administrative zones")
        
        from rasterstats import zonal_stats
        
        # Ensure zones are in same CRS as raster
        with rasterio.open(population_raster_path) as src:
            if zones.crs != src.crs:
                zones = zones.to_crs(src.crs)
        
        # Calculate zonal statistics
        stats = zonal_stats(
            zones,
            population_raster_path,
            stats=['sum', 'mean', 'count'],
            nodata=-200  # Common nodata value for population rasters
        )
        
        # Add statistics to GeoDataFrame
        zones['population_sum'] = [s['sum'] for s in stats]
        zones['population_mean'] = [s['mean'] for s in stats]
        zones['population_count'] = [s['count'] for s in stats]
        
        self.logger.info("Population extraction complete")
        return zones
    
    def calculate_population_within_distance(
        self,
        population_raster_path: str,
        facilities: gpd.GeoDataFrame,
        distance_km: float
    ) -> gpd.GeoDataFrame:
        """
        Calculate population within distance of each facility
        """
        self.logger.info(f"Calculating population within {distance_km}km of facilities")
        
        from rasterstats import zonal_stats
        
        # Create buffers around facilities
        facilities_buffered = facilities.copy()
        facilities_buffered['geometry'] = facilities.geometry.buffer(distance_km * 1000)
        
        # Extract population within buffers
        with rasterio.open(population_raster_path) as src:
            if facilities_buffered.crs != src.crs:
                facilities_buffered = facilities_buffered.to_crs(src.crs)
        
        stats = zonal_stats(
            facilities_buffered,
            population_raster_path,
            stats=['sum'],
            nodata=-200
        )
        
        facilities[f'population_within_{distance_km}km'] = [
            s['sum'] if s['sum'] is not None else 0 for s in stats
        ]
        
        self.logger.info("Population calculation complete")
        return facilities
    
    def _save_raster(
        self,
        path: str,
        data: np.ndarray,
        transform,
        crs,
        nodata=None
    ) -> None:
        """Save raster to file"""
        with rasterio.open(
            path,
            'w',
            driver='GTiff',
            height=data.shape[1],
            width=data.shape[2],
            count=1,
            dtype=data.dtype,
            transform=transform,
            crs=crs,
            nodata=nodata
        ) as dst:
            dst.write(data)
    
    def process(self, data) -> np.ndarray:
        """Default processing"""
        return data