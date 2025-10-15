from pathlib import Path
from typing import Dict, Any
import json
import yaml

class Config:
    """Centralized configuration management"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML or JSON"""
        if not self.config_path.exists():
            return self._default_config()
        
        with open(self.config_path) as f:
            if self.config_path.suffix == '.yaml':
                return yaml.safe_load(f) or {}
            else:
                return json.load(f)
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'country': 'Kenya',
            'country_code': 'KEN',
            'iso_code_3166': 'KE',
            'data_dir': 'Kenya',
            'output_dir': 'Kenya/Output',
            'crs_utm': 32737,  # UTM 37S
            'crs_wgs84': 4326,
            'center': [0.0236, 37.9062],
            'zoom_level': 6,
            'download': {
                'boundaries': True,
                'facilities': True,
                'population': False,  # Requires manual download
            },
            'processing': {
                'remove_empty_geometry': True,
                'filter_by_type': False,
                'facility_types': [],
            },
            'analysis': {
                'accessibility_threshold_km': [5, 10, 15, 20],
            },
            'visualization': {
                'generate_facility_map': True,
                'generate_accessibility_map': True,
                'generate_statistics': True,
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self.config[key]