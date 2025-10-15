import folium

class FacilityMapVisualizer(BaseVisualizer):
    """Generate facility location map"""
    
    def generate(self, facilities: gpd.GeoDataFrame, boundaries: gpd.GeoDataFrame) -> str:
        """Generate facility map"""
        self.logger.info("Generating facility map...")
        
        center = self.config['center']
        zoom = self.config['zoom_level']
        
        m = folium.Map(location=center, zoom_start=zoom)
        
        # Add boundaries
        folium.GeoJson(
            boundaries.to_json(),
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
        
        center = self.config['center']
        zoom = self.config['zoom_level']
        
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