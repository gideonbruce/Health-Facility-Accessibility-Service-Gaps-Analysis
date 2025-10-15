import requests
import json

class HealthsitesDownloader(BaseDownloader):
    """Download health facilities from healthsites.io API"""
    
    def __init__(self, output_dir: str, country_code: str = "KE"):
        super().__init__(output_dir)
        self.country_code = country_code
    
    def download(self) -> str:
        """Download health facilities"""
        self.logger.info(f"Downloading health facilities for {self.country_code}...")
        
        output_path = self.output_dir / "facilities.geojson"
        
        try:
            url = f"https://healthsites.io/api/v2/facilities/?country={self.country_code}&limit=10000"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            facilities_data = response.json()
            
            with open(output_path, 'w') as f:
                json.dump(facilities_data, f)
            
            count = len(facilities_data.get('features', []))
            self.logger.info(f"Downloaded {count} health facilities")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Failed to download facilities: {e}")
            raise
