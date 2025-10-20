import folium
import geopandas as gpd
import pandas as pd
from src.visualization.base import BaseVisualizer
from branca.colormap import LinearColormap

class FacilityMapVisualizer(BaseVisualizer):
    """Generate facility location map"""
    
    def generate(self, facilities: gpd.GeoDataFrame, boundaries: gpd.GeoDataFrame) -> str:
        """Generate facility map"""
        self.logger.info("Generating facility map...")
        bounds = boundaries.to_crs('EPSG:4326').total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = self.config['visualization'].get('zoom_level', 10)
        
        m = folium.Map(
            location=center, 
            zoom_start=zoom,
            tiles=self.config['visualization'].get('basemap', 'OpenStreetMap')
        )
        
        # Add boundaries
        folium.GeoJson(
            boundaries.copy().assign(**{
                col: boundaries[col].astype(str)
                for col in boundaries.select_dtypes(include=['datetime64']).columns
            }).to_json(),
            style_function=lambda x: {'color': 'blue', 'weight': 2, 'fillOpacity': 0.1}
        ).add_to(m)
        
        # Add facilities - USE CORRECT CONFIG KEYS
        name_field = self.config['facilities'].get('name_field', 'Facility_N')
        type_field = self.config['facilities'].get('type_field', 'Type')
        
        for idx, row in facilities.iterrows():
            coords = [row.geometry.y, row.geometry.x]
            facility_name = row.get(name_field, 'Unknown')
            facility_type = row.get(type_field, 'Unknown')
            
            folium.CircleMarker(
                coords,
                radius=5,
                popup=f"<b>{facility_name}</b><br>Type: {facility_type}",
                color='red',
                fill=True,
                fillOpacity=0.7
            ).add_to(m)
        
        # Use output.directory instead of output_dir
        output_path = self.output_dir / "facility_map.html"
        m.save(str(output_path))
        self.logger.info(f"Facility map saved to {output_path}")
        return str(output_path)


class AccessibilityMapVisualizer(BaseVisualizer):
    """Generate accessibility map with point visualization"""
    
    def generate(self, accessibility: gpd.GeoDataFrame) -> str:
        """Generate accessibility map with travel time thresholds"""
        self.logger.info("Generating accessibility map...")
        
        bounds = accessibility.to_crs('EPSG:4326').total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = self.config['visualization'].get('zoom_level', 10)
        
        m = folium.Map(
            location=center, 
            zoom_start=zoom,
            tiles=self.config['visualization'].get('basemap', 'OpenStreetMap')
        )
        
        # Get thresholds from config
        thresholds = self.config['accessibility'].get('catchment_thresholds', [15, 30, 60])
        
        # Add accessibility data as points
        for idx, row in accessibility.iterrows():
            coords = [row.geometry.y, row.geometry.x]
            
            # Use travel time if available, otherwise distance
            if 'travel_time_min' in row:
                value = row['travel_time_min']
                label = f"Travel time: {value:.1f} min"
                # Color based on travel time thresholds
                if value < thresholds[0]:
                    color = 'green'
                elif value < thresholds[1]:
                    color = 'yellow'
                elif value < thresholds[2]:
                    color = 'orange'
                else:
                    color = 'red'
            else:
                distance_km = row.get('distance_to_facility_km', row.get('distance_km', 0))
                label = f"Distance: {distance_km:.2f} km"
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
                popup=label,
                color=color,
                fill=True,
                fillOpacity=0.7
            ).add_to(m)
        
        output_path = self.output_dir / "accessibility_map.html"
        m.save(str(output_path))
        self.logger.info(f"Accessibility map saved to {output_path}")
        return str(output_path)


class PopulationChoroplethVisualizer(BaseVisualizer):
    """Generate population choropleth map by administrative boundaries"""
    
    def generate(self, population_gdf: gpd.GeoDataFrame, metric: str = None) -> str:
        """
        Generate choropleth map for population data
        
        Args:
            population_gdf: GeoDataFrame with administrative boundaries and population stats
            metric: Column name to visualize (defaults to config['population']['field'])
        """
        if metric is None:
            metric = self.config['population'].get('field', 'population')
        
        self.logger.info(f"Generating population choropleth for metric: {metric}")
        
        # Check if metric exists
        if metric not in population_gdf.columns:
            self.logger.warning(f"Metric '{metric}' not found in population data. Available: {list(population_gdf.columns)}")
            return None
        
        # Ensure WGS84
        if population_gdf.crs != 'EPSG:4326':
            population_gdf = population_gdf.to_crs('EPSG:4326')
        
        bounds = population_gdf.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = self.config['visualization'].get('zoom_level', 8)
        
        m = folium.Map(
            location=center, 
            zoom_start=zoom, 
            tiles=self.config['visualization'].get('basemap', 'OpenStreetMap')
        )
        
        # Get colormap from config
        colormap = self.config['visualization'].get('colormap', 'YlOrRd')
        
        # Reset index to ensure we have an index column
        population_gdf_indexed = population_gdf.reset_index(drop=False)
        if 'index' not in population_gdf_indexed.columns:
            population_gdf_indexed['index'] = range(len(population_gdf_indexed))
        
        # Create choropleth
        folium.Choropleth(
            geo_data=population_gdf_indexed,
            data=population_gdf_indexed,
            columns=['index', metric],
            key_on='feature.id',
            fill_color=colormap,
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=metric.replace('_', ' ').title(),
            nan_fill_color='lightgray'
        ).add_to(m)
        
        # Prepare tooltip fields - USE CORRECT CONFIG KEYS
        tooltip_fields = [metric]
        tooltip_aliases = [metric.replace('_', ' ').title()]
        
        # Add name fields from admin boundaries config
        name_field = self.config['admin_boundaries'].get('name_field', 'ward_name')
        id_field = self.config['admin_boundaries'].get('id_field', 'ward_id')
        
        if name_field and name_field in population_gdf.columns:
            tooltip_fields.insert(0, name_field)
            tooltip_aliases.insert(0, name_field.replace('_', ' ').title())
        
        if id_field and id_field in population_gdf.columns:
            tooltip_fields.append(id_field)
            tooltip_aliases.append(id_field.replace('_', ' ').title())
        
        # Add tooltips with detailed info
        folium.GeoJson(
            population_gdf,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0
            },
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                localize=True
            )
        ).add_to(m)
        
        output_path = self.output_dir / f"choropleth_{metric}.html"
        m.save(str(output_path))
        self.logger.info(f"Population choropleth saved to {output_path}")
        return str(output_path)


class AccessibilityChoroplethVisualizer(BaseVisualizer):
    """Generate accessibility choropleth by administrative region"""
    
    def generate(
        self,
        boundaries: gpd.GeoDataFrame,
        accessibility: gpd.GeoDataFrame,
        facilities: gpd.GeoDataFrame
    ) -> str:
        """
        Generate choropleth showing accessibility metrics by region
        
        Args:
            boundaries: Administrative boundaries
            accessibility: Accessibility grid with distance/time metrics
            facilities: Health facilities data
        """
        self.logger.info("Generating accessibility choropleth by region...")
        
        # Ensure same CRS
        if boundaries.crs != accessibility.crs:
            accessibility = accessibility.to_crs(boundaries.crs)
        if boundaries.crs != facilities.crs:
            facilities = facilities.to_crs(boundaries.crs)
        
        # Calculate statistics per boundary
        boundaries_with_stats = boundaries.copy()
        
        # Get configuration - USE CORRECT CONFIG KEYS
        aggregate_by = self.config['analysis'].get('aggregate_by', 'ward')
        name_field = self.config['admin_boundaries'].get('name_field', 'ward_name')
        service_radius_km = self.config['accessibility'].get('service_radius_km', 10)
        thresholds = self.config['accessibility'].get('catchment_thresholds', [15, 30, 60])
        
        # Count facilities per region
        facilities_count = []
        avg_distances = []
        avg_travel_times = []
        pop_within_threshold = []
        pop_outside_threshold = []
        
        for idx, boundary in boundaries.iterrows():
            # Count facilities in this boundary
            facilities_in_region = facilities[facilities.within(boundary.geometry)]
            facilities_count.append(len(facilities_in_region))
            
            # Calculate statistics for this region
            accessibility_in_region = accessibility[accessibility.within(boundary.geometry)]
            
            if len(accessibility_in_region) > 0:
                # Average distance
                if 'distance_to_facility_km' in accessibility_in_region.columns:
                    avg_dist = accessibility_in_region['distance_to_facility_km'].mean()
                    avg_distances.append(avg_dist)
                elif 'distance_km' in accessibility_in_region.columns:
                    avg_dist = accessibility_in_region['distance_km'].mean()
                    avg_distances.append(avg_dist)
                else:
                    avg_distances.append(None)
                
                # Average travel time
                if 'travel_time_min' in accessibility_in_region.columns:
                    avg_time = accessibility_in_region['travel_time_min'].mean()
                    avg_travel_times.append(avg_time)
                    
                    # Population within/outside threshold (use middle threshold)
                    mid_threshold = thresholds[1] if len(thresholds) > 1 else 30
                    if 'population' in accessibility_in_region.columns:
                        pop_within = accessibility_in_region[
                            accessibility_in_region['travel_time_min'] <= mid_threshold
                        ]['population'].sum()
                        pop_outside = accessibility_in_region[
                            accessibility_in_region['travel_time_min'] > mid_threshold
                        ]['population'].sum()
                        pop_within_threshold.append(pop_within)
                        pop_outside_threshold.append(pop_outside)
                    else:
                        pop_within_threshold.append(0)
                        pop_outside_threshold.append(0)
                else:
                    avg_travel_times.append(None)
                    pop_within_threshold.append(0)
                    pop_outside_threshold.append(0)
            else:
                avg_distances.append(None)
                avg_travel_times.append(None)
                pop_within_threshold.append(0)
                pop_outside_threshold.append(0)
        
        # Add statistics to boundaries
        boundaries_with_stats['facility_count'] = facilities_count
        if any(d is not None for d in avg_distances):
            boundaries_with_stats['avg_distance_km'] = avg_distances
        if any(t is not None for t in avg_travel_times):
            boundaries_with_stats['avg_travel_time_min'] = avg_travel_times
            boundaries_with_stats['pop_within_threshold'] = pop_within_threshold
            boundaries_with_stats['pop_outside_threshold'] = pop_outside_threshold
        
        # Convert to WGS84 for mapping
        boundaries_with_stats = boundaries_with_stats.to_crs('EPSG:4326')
        
        bounds = boundaries_with_stats.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = self.config['visualization'].get('zoom_level', 8)
        
        m = folium.Map(
            location=center, 
            zoom_start=zoom,
            tiles=self.config['visualization'].get('basemap', 'OpenStreetMap')
        )
        
        # Determine which metric to use for choropleth
        if 'avg_travel_time_min' in boundaries_with_stats.columns:
            metric = 'avg_travel_time_min'
            legend_name = 'Average Travel Time (minutes)'
        elif 'avg_distance_km' in boundaries_with_stats.columns:
            metric = 'avg_distance_km'
            legend_name = 'Average Distance (km)'
        else:
            metric = 'facility_count'
            legend_name = 'Facility Count'
        
        # Create choropleth
        folium.Choropleth(
            geo_data=boundaries_with_stats,
            data=boundaries_with_stats,
            columns=['index', metric],
            key_on='feature.id',
            fill_color='RdYlGn_r',  # Red for poor access, green for good
            fill_opacity=0.7,
            line_opacity=0.5,
            legend_name=legend_name,
            nan_fill_color='lightgray'
        ).add_to(m)
        
        # Prepare tooltip fields
        tooltip_fields = [metric, 'facility_count']
        tooltip_aliases = [legend_name, 'Facility Count']
        
        # Add additional fields
        if 'pop_within_threshold' in boundaries_with_stats.columns:
            tooltip_fields.extend(['pop_within_threshold', 'pop_outside_threshold'])
            tooltip_aliases.extend(['Pop Within Threshold', 'Pop Outside Threshold'])
        
        if name_field in boundaries_with_stats.columns:
            tooltip_fields.insert(0, name_field)
            tooltip_aliases.insert(0, name_field.replace('_', ' ').title())
        
        # Add interactive tooltips
        folium.GeoJson(
            boundaries_with_stats,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'black',
                'weight': 1.5,
                'fillOpacity': 0
            },
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                localize=True
            )
        ).add_to(m)
        
        # Add map title
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 400px; height: 50px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:16px; padding: 10px">
        <b>{self.config['visualization'].get('map_title', 'Health Service Accessibility')}</b><br>
        {self.config['project']['region']}, {self.config['project']['country']}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        output_path = self.output_dir / "accessibility_choropleth.html"
        m.save(str(output_path))
        self.logger.info(f"Accessibility choropleth saved to {output_path}")
        return str(output_path)


class ServiceGapChoroplethVisualizer(BaseVisualizer):
    """Generate service gap choropleth highlighting underserved areas"""
    
    def generate(
        self,
        boundaries: gpd.GeoDataFrame,
        accessibility: gpd.GeoDataFrame
    ) -> str:
        """
        Generate choropleth highlighting service gaps
        
        Args:
            boundaries: Administrative boundaries
            accessibility: Accessibility grid with population and metrics
        """
        self.logger.info("Generating service gap choropleth...")
        
        # Ensure same CRS
        if boundaries.crs != accessibility.crs:
            accessibility = accessibility.to_crs(boundaries.crs)
        
        boundaries_with_gaps = boundaries.copy()
        
        # Get gap definition from config
        gap_threshold = self.config['accessibility']['catchment_thresholds'][1]  # Default to 30 min
        min_pop_gap = self.config['accessibility'].get('min_population_gap', 1000)
        
        gap_populations = []
        service_gap_scores = []
        
        for idx, boundary in boundaries.iterrows():
            accessibility_in_region = accessibility[accessibility.within(boundary.geometry)]
            
            if len(accessibility_in_region) > 0 and 'travel_time_min' in accessibility_in_region.columns:
                # Calculate population outside threshold
                if 'population' in accessibility_in_region.columns:
                    gap_pop = accessibility_in_region[
                        accessibility_in_region['travel_time_min'] > gap_threshold
                    ]['population'].sum()
                    
                    total_pop = accessibility_in_region['population'].sum()
                    
                    # Calculate gap score (percentage)
                    gap_score = (gap_pop / total_pop * 100) if total_pop > 0 else 0
                    
                    gap_populations.append(gap_pop)
                    service_gap_scores.append(gap_score)
                else:
                    gap_populations.append(0)
                    service_gap_scores.append(0)
            else:
                gap_populations.append(0)
                service_gap_scores.append(0)
        
        boundaries_with_gaps['gap_population'] = gap_populations
        boundaries_with_gaps['gap_score_pct'] = service_gap_scores
        
        # Convert to WGS84
        boundaries_with_gaps = boundaries_with_gaps.to_crs('EPSG:4326')
        
        bounds = boundaries_with_gaps.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = self.config['visualization'].get('zoom_level', 8)
        
        m = folium.Map(location=center, zoom_start=zoom)
        
        # Create choropleth for service gaps
        folium.Choropleth(
            geo_data=boundaries_with_gaps,
            data=boundaries_with_gaps,
            columns=['index', 'gap_score_pct'],
            key_on='feature.id',
            fill_color='Reds',  # Red intensity shows gap severity
            fill_opacity=0.7,
            line_opacity=0.5,
            legend_name=f'Service Gap (% Pop >{gap_threshold}min)',
            nan_fill_color='lightgray'
        ).add_to(m)
        
        # Add tooltips - USE CORRECT CONFIG KEY
        name_field = self.config['admin_boundaries'].get('name_field', 'ward_name')
        tooltip_fields = ['gap_score_pct', 'gap_population']
        tooltip_aliases = ['Gap Score (%)', 'Underserved Population']
        
        if name_field in boundaries_with_gaps.columns:
            tooltip_fields.insert(0, name_field)
            tooltip_aliases.insert(0, name_field.replace('_', ' ').title())
        
        folium.GeoJson(
            boundaries_with_gaps,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'black',
                'weight': 1.5,
                'fillOpacity': 0
            },
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                localize=True
            )
        ).add_to(m)
        
        output_path = self.output_dir / "service_gap_choropleth.html"
        m.save(str(output_path))
        self.logger.info(f"Service gap choropleth saved to {output_path}")
        return str(output_path)