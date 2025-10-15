from src.downloader.base import BaseDownloader


class PopulationDownloader(BaseDownloader):
    """Handle population raster data"""
    
    def download(self) -> str:
        """Placeholder for population data"""
        self.logger.info("Population data requires manual download from GHS-POP")
        self.logger.info("Visit: https://ghsl.jrc.ec.europa.eu/download.php")
        return str(self.output_dir)