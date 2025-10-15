from typing import List, Optional, cast
import numpy as np
from shapely.geometry import Point
import geopandas as gpd

from src.analysis.base import BaseAnalyzer

class AccessibilityAnalyzer(BaseAnalyzer):
    """Analyze healthcare accessibility"""
    
    def calculate_distances(
        self,
        facilities: gpd.GeoDataFrame,
        population: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Calculate distance from population to nearest facility"""
        self.logger.info("Calculating distances to nearest facilities...")
        
        population['nearest_facility_idx'] = population.geometry.apply(
            lambda geom: facilities.distance(geom).argmin()
        )
        population['distance_to_facility_m'] = population.geometry.apply(
            lambda geom: facilities.distance(geom).min()
        )
        population['distance_to_facility_km'] = (
            population['distance_to_facility_m'] / 1000
        )
        
        self.logger.info("Distance calculation complete")
        return population
    
    def classify_accessibility(
        self,
        population: gpd.GeoDataFrame,
        thresholds_km: Optional[List[float]] = None
    ) -> gpd.GeoDataFrame:
        """Classify accessibility by threshold"""
        if thresholds_km is None:
            thresholds_km = cast(List[float], self.config['analysis']['accessibility_threshold_km'])
        
        self.logger.info(f"Classifying accessibility with thresholds: {thresholds_km}")
        
        distance = population['distance_to_facility_km']
        
        for threshold in sorted(thresholds_km):
            col_name = f'within_{threshold}km'
            population[col_name] = distance <= threshold
        
        return population
    
    def create_population_grid(
        self,
        boundaries: gpd.GeoDataFrame,
        grid_size: int = 20
    ) -> gpd.GeoDataFrame:
        """Create grid of population centers"""
        self.logger.info(f"Creating population grid ({grid_size}x{grid_size})...")
        
        minx, miny, maxx, maxy = boundaries.total_bounds
        points = [
            Point(x, y)
            for x in np.linspace(minx, maxx, grid_size)
            for y in np.linspace(miny, maxy, grid_size)
        ]
        
        grid = gpd.GeoDataFrame(
            {'geometry': points},
            crs=boundaries.crs
        )
        
        self.logger.info(f"Created {len(grid)} grid points")
        return grid
    
    def analyze(self, facilities: gpd.GeoDataFrame, population: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Complete accessibility analysis"""
        pop_with_distances = self.calculate_distances(facilities, population)
        pop_classified = self.classify_accessibility(pop_with_distances)
        return pop_classified