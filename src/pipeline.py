from src.logger import Logger
from pathlib import Path
import geopandas as gpd
from src.config import Config
from src.population.zonal_extractor import PopulationZonalExtractor
from src.loaders.facilities_loader import FacilitiesLoader
from src.loaders.roads_loader import RoadsLoader

class Pipeline:
    """Main orchestration pipeline"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.get('Pipeline')
        
        # Create directories
        Path(self.config['data_dir']).mkdir(exist_ok=True)
        Path(self.config['output_dir']).mkdir(exist_ok=True)
    
    def download_data(self) -> tuple:
        """Download required data skips if disabled"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP 1: Downloading Data")
        self.logger.info("="*70)
        
        download_config = self.config.get('download', {})
        if not download_config.get('enabled', False):
            self.logger.info("[INFO] Download disabled. Using local data.")
            data_dir = Path(self.config['data_dir'])
            boundaries_path = data_dir / "Administrative_boundaries"
            facilities_path = data_dir / "Health_facilities"
            return boundaries_path, facilities_path
        
        data_dir = Path(self.config['data_dir'])
        boundaries_path = None
        facilities_path = None
        
        if download_config.get('boundaries', False):
            from src.downloader.gadm import GADMDownloader
            downloader = GADMDownloader(str(data_dir / "Administrative_boundaries"))
            downloader.download()
            boundaries_path = data_dir / "Administrative_boundaries"
        
        if download_config.get('facilities', False):
            from src.downloader.healthsites import HealthsitesDownloader
            downloader = HealthsitesDownloader(
                str(data_dir / "Health_facilities"),
                self.config['iso_code_3166']
            )
            facilities_path = downloader.download()
        
        return boundaries_path, facilities_path
    
    def process_data(self) -> tuple:
        """Load and process local administrative boundaries and health facilities"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP 2: Processing Data")
        self.logger.info("="*70)
        
        from src.processor.vector import VectorProcessor
        from src.loaders.facilities_loader import FacilitiesLoader
        from pathlib import Path

        processor = VectorProcessor(self.config)
        data_dir = Path(self.config['data_dir'])
        
        # --- Load administrative boundaries from local shapefiles ---
        boundary_files = list(data_dir.glob("administrative/*.shp"))
        if not boundary_files:
            raise FileNotFoundError("No shapefiles found in Administrative_boundaries folder")
        shp_path = boundary_files[0]
        
        self.logger.info(f"Loading administrative boundaries from: {shp_path}")
        boundaries = processor.load_shapefile(str(shp_path))
        boundaries = processor.reproject(boundaries, self.config['crs_utm'])
        
        # --- Load health facilities from local CSV ---
        facilities_csv = self.config['facilities']['csv']
        facilities_geojson = data_dir / "Health_facilities" / "facilities.geojson"

        self.logger.info(f"Loading health facilities from CSV: {facilities_csv}")
        loader = FacilitiesLoader(facilities_csv)
        facilities = loader.load()

        # Match CRS with boundaries
        if facilities.crs != boundaries.crs:
            facilities = facilities.to_crs(boundaries.crs)

        facilities_geojson.parent.mkdir(parents=True, exist_ok=True)
        # Save GeoJSON for reuse (optional)
        facilities.to_file(facilities_geojson, driver="GeoJSON")

        # --- Post-process facilities ---
        facilities = processor.remove_empty_geometry(facilities)
        facilities = processor.clip_to_bounds(facilities, boundaries)

        self.logger.info(f"✓ Loaded {len(facilities)} facilities after processing")
        return boundaries, facilities
    
    def load_roads(self) -> gpd.GeoDataFrame:
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP X: Loading Road Network")
        self.logger.info("="*70)
        roads_loader = RoadsLoader({**dict(self.config), "logger": self.logger})
        roads = roads_loader.load()
        return roads

    def analyze_accessibility(self, facilities: gpd.GeoDataFrame, boundaries: gpd.GeoDataFrame) -> tuple:
        """Analyze accessibility"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP 3: Analyzing Accessibility")
        self.logger.info("="*70)
        
        from src.analysis.accessibility import AccessibilityAnalyzer
        from src.analysis.statistics import StatisticsAnalyzer

        # Create population grid
        accessibility_analyzer = AccessibilityAnalyzer(self.config)
        population_grid = accessibility_analyzer.create_population_grid(boundaries)
        
        # Calculate accessibility
        accessibility = accessibility_analyzer.analyze(facilities, population_grid)
        
        # Calculate statistics
        stats_analyzer = StatisticsAnalyzer(self.config)
        stats = stats_analyzer.analyze(facilities, accessibility)
        
        return accessibility, stats
    
    def visualize(
        self,
        facilities: gpd.GeoDataFrame,
        boundaries: gpd.GeoDataFrame,
        accessibility: gpd.GeoDataFrame,
        population: gpd.GeoDataFrame = None
    ) -> None:
        """Generate visualizations including choropleths"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP 4: Generating Visualizations")
        self.logger.info("="*70)
        
        from src.visualization.maps import (
            FacilityMapVisualizer,
            AccessibilityMapVisualizer,
            PopulationChoroplethVisualizer,
            AccessibilityChoroplethVisualizer
        )
        
        viz_config = self.config['visualization']
        output_dir = self.config['output_dir']
        
        # Generate facility map
        if viz_config.get('generate_facility_map', True):
            facilities_wgs84 = facilities.to_crs(epsg=4326)
            boundaries_wgs84 = boundaries.to_crs(epsg=4326)
            viz = FacilityMapVisualizer(self.config, output_dir)
            viz.generate(facilities_wgs84, boundaries_wgs84)
        
        # Generate accessibility point map
        if viz_config.get('generate_accessibility_map', True):
            accessibility_wgs84 = accessibility.to_crs(epsg=4326)
            viz = AccessibilityMapVisualizer(self.config, output_dir)
            viz.generate(accessibility_wgs84)
        
        # Generate population choropleth
        if viz_config.get('generate_population_choropleth', True) and population is not None:
            viz = PopulationChoroplethVisualizer(self.config, output_dir)
            viz.generate(population, metric='population')
            
            # If population density exists, create that choropleth too
            if 'population_density' in population.columns:
                viz.generate(population, metric='population_density')
        
        # Generate accessibility choropleth by administrative region
        if viz_config.get('generate_accessibility_choropleth', True):
            viz = AccessibilityChoroplethVisualizer(self.config, output_dir)
            viz.generate(boundaries, accessibility, facilities)
    
    def save_outputs(
        self,
        boundaries: gpd.GeoDataFrame,
        facilities: gpd.GeoDataFrame,
        accessibility: gpd.GeoDataFrame,
        stats: dict,
        population: gpd.GeoDataFrame = None,
        roads=None
    ) -> None:
        """Save processed data and results"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP 5: Saving Outputs")
        self.logger.info("="*70)
        
        output_dir = Path(self.config['output_dir'])
        
        facilities.to_file(
            str(output_dir / "facilities_processed.geojson"),
            driver='GeoJSON'
        )
        boundaries.to_file(
            str(output_dir / "boundaries.geojson"),
            driver='GeoJSON'
        )
        accessibility.to_file(
            str(output_dir / "accessibility_grid.geojson"),
            driver='GeoJSON'
        )
        
        if population is not None:
            population.to_file(
                str(output_dir / "population_by_region.geojson"),
                driver='GeoJSON'
            )
            self.logger.info("  Population data saved to output folder")
        
        if roads is not None:
            roads.to_file(output_dir / "roads.geojson", driver='GeoJSON')
            self.logger.info("  Roads saved to output folder")
        
        from src.analysis.statistics import StatisticsAnalyzer
        stats_analyzer = StatisticsAnalyzer(self.config)
        stats_analyzer.save_stats(stats, str(output_dir / "statistics.json"))
        
        self.logger.info("All outputs saved")
    
    def run(self) -> dict:
        """Execute complete pipeline"""
        self.logger.info("\n" + "="*70)
        self.logger.info("KENYA HEALTHCARE ACCESSIBILITY ANALYSIS PIPELINE")
        self.logger.info("="*70)
        
        try:
            # STEP 1: Data acquisition
            self.download_data()
            
            # STEP 2: Data processing
            boundaries, facilities = self.process_data()

            # STEP 3: Population zonal statistics
            from src.population.zonal_extractor import PopulationZonalExtractor
            
            pop_raster_path = self.config['population']['raster']
            pop_output_path = self.config['population']['zonal_output']

            self.logger.info("\n" + "="*70)
            self.logger.info("STEP 3: Calculating Population Zonal Statistics")
            self.logger.info("="*70)
            data_dir = Path(self.config['data_dir'])
            temp_boundaries_path = data_dir / "temp_boundaries.geojson"
            boundaries.to_file(temp_boundaries_path, driver="GeoJSON")

            extractor = PopulationZonalExtractor(str(temp_boundaries_path), pop_raster_path)
            pop_gdf = extractor.run(pop_output_path)

            self.logger.info(f"✓ Population zonal statistics saved to: {pop_output_path}")

            # STEP 4: Accessibility analysis
            accessibility, stats = self.analyze_accessibility(facilities, boundaries)

            # STEP 5: Visualization (now includes choropleths)
            self.visualize(facilities, boundaries, accessibility, pop_gdf)

            # STEP 6: Save outputs
            self.save_outputs(boundaries, facilities, accessibility, stats, pop_gdf)

            self.logger.info("\n" + "="*70)
            self.logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("="*70)

            return {
                'boundaries': boundaries,
                'facilities': facilities,
                'population': pop_gdf,
                'accessibility': accessibility,
                'statistics': stats
            }

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)