from typing import Optional
import requests
from pathlib import Path

from src.downloader.base import BaseDownloader

class DEMDownloader(BaseDownloader):
    """
    Download Digital Elevation Model (DEM) data
    
    Options:
    1. SRTM (Shuttle Radar Topography Mission) - 30m or 90m resolution
    2. ASTER GDEM - Global DEM
    3. ALOS World 3D - 30m resolution
    """
    
    def __init__(self, output_dir: str, bounds: Optional[tuple] = None):
        super().__init__(output_dir)
        self.bounds = bounds  # (minx, miny, maxx, maxy)
    
    def download_srtm_tiles(self, tile_list: list) -> list:
        """
        Download SRTM tiles
        
        Args:
            tile_list: List of SRTM tile names (e.g., ['N00E036', 'N00E037'])
        
        Note: SRTM data requires USGS EarthExplorer account
        This is a placeholder - actual implementation depends on data source
        """
        self.logger.info(f"Downloading {len(tile_list)} SRTM tiles")
        self.logger.warning(
            "SRTM download requires USGS credentials. "
            "Please download manually from: https://earthexplorer.usgs.gov/"
        )
        
        downloaded_files = []
        for tile in tile_list:
            tile_path = self.output_dir / f"{tile}.tif"
            if tile_path.exists():
                downloaded_files.append(str(tile_path))
                self.logger.info(f"Found existing tile: {tile}")
        
        return downloaded_files
    
    def download_from_opentopography(
        self,
        bounds: tuple,
        dem_type: str = 'SRTMGL1'
    ) -> str:
        """
        Download DEM from OpenTopography API
        
        Args:
            bounds: (west, south, east, north)
            dem_type: 'SRTMGL1' (30m), 'SRTMGL3' (90m), 'AW3D30'
        
        Note: Requires OpenTopography API key
        """
        self.logger.info(f"Downloading DEM from OpenTopography: {dem_type}")
        
        api_key = "YOUR_API_KEY"  # Load from config
        base_url = "https://portal.opentopography.org/API/globaldem"
        
        params = {
            'demtype': dem_type,
            'west': bounds[0],
            'south': bounds[1],
            'east': bounds[2],
            'north': bounds[3],
            'outputFormat': 'GTiff',
            'API_Key': api_key
        }
        
        output_path = self.output_dir / f"dem_{dem_type}.tif"
        
        try:
            self.logger.info(f"Requesting DEM for bounds: {bounds}")
            response = requests.get(base_url, params=params, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"DEM downloaded to {output_path}")
            return str(output_path)
        
        except Exception as e:
            self.logger.error(f"Failed to download DEM: {e}")
            self.logger.info(
                "Alternative: Download manually from "
                "https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1"
            )
            raise
    
    def download(self) -> str:
        """Download DEM data"""
        self.logger.info("DEM data download options:")
        self.logger.info("1. SRTM: https://earthexplorer.usgs.gov/")
        self.logger.info("2. OpenTopography: https://portal.opentopography.org/")
        self.logger.info("3. ALOS: https://www.eorc.jaxa.jp/ALOS/en/aw3d30/")
        
        if self.bounds:
            self.logger.info(f"Recommended bounds for Kenya: {self.bounds}")
        
        return str(self.output_dir)