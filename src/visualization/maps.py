import folium
import geopandas as gpd
from src.visualization.base import BaseVisualizer

class FacilityMapVisualizer(BaseVisualizer):
    """Generate facility location map"""
    
    def generate(self, facilities: gpd.GeoDataFrame, boundaries: gpd.GeoDataFrame) -> str:
        """Generate facility map"""
        self.logger.info("Generating facility map...")
        bounds = boundaries.to_crs('EPSG:4326').total_bounds  # [minx, miny, maxx, maxy]
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]  # [lat, lon]
        zoom = self.config.get('zoom_level', 10)  # Default to 10 if not specified
        
        m = folium.Map(location=center, zoom_start=zoom)
        
        # Add boundaries
        folium.GeoJson(
            boundaries.copy().assign(**{
                col: boundaries[col].astype(str)
                for col in boundaries.select_dtypes(include=['datetime64']).columns
            }).to_json(),
            style_function=lambda x: {'color': 'blue', 'weight': 2, 'fillOpacity': 0.1}
        ).add_to(m)
        
        # Add facilities
        for idx, row in facilities.iterrows():
            coords = [row.geometry.y, row.geometry.x]
            folium.CircleMarker(
                coords,
                radius=5,
                popup=f"Facility: {row.get('name', 'Unknown')}",
                color='red',
                fill=True,
                fillOpacity=0.7
            ).add_to(m)
        
        output_path = self.output_dir / "facility_map.html"
        m.save(str(output_path))
        self.logger.info(f"Facility map saved to {output_path}")
        return str(output_path)


class AccessibilityMapVisualizer(BaseVisualizer):
    """Generate accessibility choropleth map"""
    
    def generate(self, accessibility: gpd.GeoDataFrame) -> str:
        """Generate accessibility map"""
        self.logger.info("Generating accessibility map...")
        
        bounds = accessibility.to_crs('EPSG:4326').total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = self.config.get('zoom_level', 10)
        
        m = folium.Map(location=center, zoom_start=zoom)
        
        # Add accessibility data
        for idx, row in accessibility.iterrows():
            coords = [row.geometry.y, row.geometry.x]
            distance_km = row['distance_to_facility_km']
            
            # Color based on distance
            if distance_km < 5:
                color = 'green'
            elif distance_km < 10:
                color = 'yellow'
            elif distance_km < 20:
                color = 'orange'
            else:
                color = 'red'
            
            folium.CircleMarker(
                coords,
                radius=5,
                popup=f"Distance: {distance_km:.2f} km",
                color=color,
                fill=True,
                fillOpacity=0.7
            ).add_to(m)
        
        output_path = self.output_dir / "accessibility_map.html"
        m.save(str(output_path))
        self.logger.info(f"Accessibility map saved to {output_path}")
        return str(output_path)