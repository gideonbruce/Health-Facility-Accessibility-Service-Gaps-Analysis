import urllib.request
import zipfile

class GADMDownloader(BaseDownloader):
    """Download administrative boundaries from GADM/Natural Earth"""
    
    def download(self) -> str:
        """Download administrative boundaries"""
        self.logger.info("Downloading administrative boundaries...")
        
        url = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip"
        zip_path = self.output_dir / "admin_boundaries.zip"
        
        try:
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.output_dir)
            
            self.logger.info(f"Downloaded boundaries to {self.output_dir}")
            zip_path.unlink()  # Clean up zip
            return str(self.output_dir)
        except Exception as e:
            self.logger.error(f"Failed to download boundaries: {e}")
            raise
