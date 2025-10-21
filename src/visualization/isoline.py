import folium
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, MultiLineString
from scipy.interpolate import griddata
from shapely.ops import linemerge, unary_union
from src.visualization.base import BaseVisualizer


class IsolineMapVisualizer(BaseVisualizer):
    """Generate isoline (isochrone/isodistance) map showing travel time or distance contours"""
    
    def generate(
        self,
        accessibility: gpd.GeoDataFrame,
        boundaries: gpd.GeoDataFrame,
        facilities: gpd.GeoDataFrame = None
    ) -> str:
        """
        Generate isoline map with contours for travel time or distance
        
        Args:
            accessibility: Accessibility grid with distance/time metrics
            boundaries: Administrative boundaries for clipping
            facilities: Optional health facilities to overlay
        """
        self.logger.info("Generating isoline map...")
        
        # Ensure consistent CRS (use projected CRS for accurate calculations)
        target_crs = self.config['crs_utm']
        if accessibility.crs != target_crs:
            accessibility = accessibility.to_crs(target_crs)
        if boundaries.crs != target_crs:
            boundaries = boundaries.to_crs(target_crs)
        if facilities is not None and facilities.crs != target_crs:
            facilities = facilities.to_crs(target_crs)
        
        # Determine which metric to use
        if 'travel_time_min' in accessibility.columns:
            metric = 'travel_time_min'
            metric_label = 'Travel Time (minutes)'
            thresholds = self.config['accessibility'].get('catchment_thresholds', [15, 30, 60])
        elif 'distance_to_facility_km' in accessibility.columns:
            metric = 'distance_to_facility_km'
            metric_label = 'Distance (km)'
            thresholds = [5, 10, 20]
        elif 'distance_km' in accessibility.columns:
            metric = 'distance_km'
            metric_label = 'Distance (km)'
            thresholds = [5, 10, 20]
        else:
            self.logger.error("No suitable metric found for isoline generation")
            return None
        
        # Extract coordinates and values
        coords = np.array([[geom.x, geom.y] for geom in accessibility.geometry])
        values = accessibility[metric].values
        
        # Remove any NaN or infinite values
        valid_mask = np.isfinite(values)
        coords = coords[valid_mask]
        values = values[valid_mask]
        
        if len(coords) == 0:
            self.logger.error("No valid data points for isoline generation")
            return None
        
        # Create interpolation grid
        bounds = boundaries.total_bounds
        grid_resolution = self.config['accessibility'].get('grid_resolution', 1000)
        x_range = np.arange(bounds[0], bounds[2], grid_resolution)
        y_range = np.arange(bounds[1], bounds[3], grid_resolution)
        grid_x, grid_y = np.meshgrid(x_range, y_range)
        
        self.logger.info(f"Interpolating {len(coords)} points onto {grid_x.shape} grid...")
        
        # Interpolate values onto grid
        try:
            grid_values = griddata(
                coords, 
                values, 
                (grid_x, grid_y), 
                method='cubic',
                fill_value=np.nan
            )
        except Exception as e:
            self.logger.warning(f"Cubic interpolation failed, falling back to linear: {e}")
            grid_values = griddata(
                coords, 
                values, 
                (grid_x, grid_y), 
                method='linear',
                fill_value=np.nan
            )
        
        # Generate contours using matplotlib's contour function
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
        
        fig, ax = plt.subplots(figsize=(1, 1))
        contour_set = ax.contour(grid_x, grid_y, grid_values, levels=thresholds)
        plt.close(fig)
        
        # Convert matplotlib contours to GeoDataFrame
        isolines = []
        isoline_levels = []
        
        # Extract contour paths (compatible with newer matplotlib versions)
        for i, level in enumerate(contour_set.levels):
            # Get paths from the contour set
            paths = contour_set.get_paths()
            if hasattr(contour_set, 'collections'):
                # Older matplotlib API
                collection = contour_set.collections[i]
                paths = collection.get_paths()
            else:
                # Newer matplotlib API - get segments directly
                try:
                    segs = contour_set.allsegs[i]
                    for seg in segs:
                        if len(seg) > 2:
                            line = LineString(seg)
                            isolines.append(line)
                            isoline_levels.append(level)
                    continue
                except (AttributeError, IndexError):
                    pass
            
            # Fallback for older API
            for path in paths:
                vertices = path.vertices
                if len(vertices) > 2:
                    line = LineString(vertices)
                    isolines.append(line)
                    isoline_levels.append(level)
        
        if not isolines:
            self.logger.warning("No isolines generated")
            return None
        
        # Create GeoDataFrame from isolines
        isolines_gdf = gpd.GeoDataFrame({
            metric: isoline_levels,
            'geometry': isolines
        }, crs=target_crs)
        
        # Clip isolines to boundaries
        boundary_union = boundaries.unary_union
        isolines_gdf = isolines_gdf[isolines_gdf.intersects(boundary_union)]
        isolines_gdf['geometry'] = isolines_gdf.geometry.intersection(boundary_union)
        
        # Convert to WGS84 for mapping
        isolines_gdf = isolines_gdf.to_crs('EPSG:4326')
        boundaries_wgs84 = boundaries.to_crs('EPSG:4326')
        
        # Create map
        bounds_wgs84 = boundaries_wgs84.total_bounds
        center = [(bounds_wgs84[1] + bounds_wgs84[3]) / 2, (bounds_wgs84[0] + bounds_wgs84[2]) / 2]
        zoom = self.config['visualization'].get('zoom_level', 10)
        
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles=self.config['visualization'].get('basemap', 'OpenStreetMap')
        )
        
        boundaries_for_map = boundaries_wgs84[['geometry']].copy()
        #for col in boundaries_for_map.columns:
            #if boundaries_for_map[col].dtype == 'object':
                #try:
                    #convert timestamp
                   # boundaries_for_map[col] = boundaries_for_map[col].astype(str)
                #except:
                    #pass
        # Add boundaries
        folium.GeoJson(
            boundaries_for_map,
            style_function=lambda x: {
                'color': 'gray',
                'weight': 2,
                'fillOpacity': 0.05
            }
        ).add_to(m)
        
        # Define colors for isolines (green to red)
        colors = ['#00ff00', '#ffff00', '#ff9900', '#ff0000']
        
        # Add isolines with different colors per threshold
        for i, threshold in enumerate(sorted(set(isoline_levels))):
            color = colors[min(i, len(colors)-1)]
            isoline_subset = isolines_gdf[isolines_gdf[metric] == threshold]
            
            folium.GeoJson(
                isoline_subset,
                style_function=lambda x, c=color: {
                    'color': c,
                    'weight': 3,
                    'opacity': 0.8
                },
                tooltip=f"{metric_label}: {threshold}"
            ).add_to(m)
        
        # Add facilities if provided
        if facilities is not None:
            facilities_wgs84 = facilities.to_crs('EPSG:4326')
            name_field = self.config['facilities'].get('name_field', 'Facility_N')
            
            for idx, row in facilities_wgs84.iterrows():
                coords = [row.geometry.y, row.geometry.x]
                facility_name = row.get(name_field, 'Unknown')
                
                folium.CircleMarker(
                    coords,
                    radius=6,
                    popup=f"<b>{facility_name}</b>",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.9
                ).add_to(m)
        
        # Add legend
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>{metric_label} Isolines</b><br>
        '''
        
        for i, threshold in enumerate(sorted(set(isoline_levels))):
            color = colors[min(i, len(colors)-1)]
            legend_html += f'<i style="background:{color};width:20px;height:3px;display:inline-block;"></i> {threshold}<br>'
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add title
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 400px; height: 50px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:16px; padding: 10px">
        <b>Healthcare Accessibility Isolines</b><br>
        {self.config['project']['region']}, {self.config['project']['country']}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save map
        output_path = self.output_dir / "isoline_map.html"
        m.save(str(output_path))
        self.logger.info(f"Isoline map saved to {output_path}")
        
        # Save isolines as GeoJSON for reuse
        isolines_output_path = self.output_dir / "isolines.geojson"
        isolines_gdf.to_file(isolines_output_path, driver='GeoJSON')
        self.logger.info(f"Isolines saved to {isolines_output_path}")
        
        return str(output_path)