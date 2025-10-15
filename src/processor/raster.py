import rasterio
from rasterio.mask import mask
import numpy as np

class RasterProcessor(BaseProcessor):
    """Process raster (GeoTIFF, etc.) data"""
    
    def load_raster(self, raster_path: str) -> tuple:
        """Load raster data"""
        self.logger.info(f"Loading raster: {raster_path}")
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            transform = src.transform
            crs = src.crs
        return data, transform, crs
    
    def clip_raster(
        self,
        raster_path: str,
        clip_bounds: gpd.GeoDataFrame,
        output_path: str
    ) -> str:
        """Clip raster to bounds"""
        self.logger.info("Clipping raster to boundaries")
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
                src.crs
            )
        
        self.logger.info(f"Clipped raster saved to {output_path}")
        return output_path
    
    def _save_raster(self, path: str, data: np.ndarray, transform, crs) -> None:
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
            crs=crs
        ) as dst:
            dst.write(data)
    
    def process(self, data) -> np.ndarray:
        """Default processing"""
        return data