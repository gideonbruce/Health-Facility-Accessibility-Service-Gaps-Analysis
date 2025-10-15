import json
from typing import Dict

class StatisticsAnalyzer(BaseAnalyzer):
    """Generate summary statistics"""
    
    def calculate_stats(
        self,
        facilities: gpd.GeoDataFrame,
        accessibility: gpd.GeoDataFrame
    ) -> Dict:
        """Calculate summary statistics"""
        self.logger.info("Calculating summary statistics...")
        
        thresholds = self.config['analysis']['accessibility_threshold_km']
        
        stats = {
            'total_facilities': int(len(facilities)),
            'distance_statistics': {
                'mean_km': float(accessibility['distance_to_facility_km'].mean()),
                'median_km': float(accessibility['distance_to_facility_km'].median()),
                'std_km': float(accessibility['distance_to_facility_km'].std()),
                'min_km': float(accessibility['distance_to_facility_km'].min()),
                'max_km': float(accessibility['distance_to_facility_km'].max()),
            },
            'accessibility_by_threshold': {}
        }
        
        for threshold in thresholds:
            col_name = f'within_{threshold}km'
            count = accessibility[col_name].sum()
            percentage = (count / len(accessibility)) * 100
            stats['accessibility_by_threshold'][f'{threshold}km'] = {
                'count': int(count),
                'percentage': float(percentage)
            }
        
        self.logger.info("Statistics calculated")
        return stats
    
    def save_stats(self, stats: Dict, output_path: str) -> None:
        """Save statistics to JSON"""
        self.logger.info(f"Saving statistics to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def analyze(self, facilities: gpd.GeoDataFrame, accessibility: gpd.GeoDataFrame) -> Dict:
        """Complete statistics analysis"""
        return self.calculate_stats(facilities, accessibility)