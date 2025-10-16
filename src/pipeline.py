from src.logger import Logger
from pathlib import Path
import geopandas as gpd
from src.config import Config
from src.population.zonal_extractor import PopulationZonalExtractor
from src.loaders.facilities_loader import FacilitiesLoader

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
        #boundaries = processor.filter_by_country(
            #boundaries,
            #self.config['country_code']
        #)
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
        accessibility: gpd.GeoDataFrame
    ) -> None:
        """Generate visualizations"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STEP 4: Generating Visualizations")
        self.logger.info("="*70)
        
        from src.visualization.maps import FacilityMapVisualizer, AccessibilityMapVisualizer
        
        viz_config = self.config['visualization']
        output_dir = self.config['output_dir']
        
        if viz_config['generate_facility_map']:
            viz = FacilityMapVisualizer(self.config, output_dir)
            viz.generate(facilities, boundaries)
        
        if viz_config['generate_accessibility_map']:
            viz = AccessibilityMapVisualizer(self.config, output_dir)
            viz.generate(accessibility)
    
    def save_outputs(
        self,
        boundaries: gpd.GeoDataFrame,
        facilities: gpd.GeoDataFrame,
        accessibility: gpd.GeoDataFrame,
        stats: dict
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

            # STEP 3: Population zonal statistics (NEW)
            from src.population.zonal_extractor import PopulationZonalExtractor
            
            pop_raster_path = self.config['population']['raster']  # path from config.yaml
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

            # STEP 5: Visualization
            self.visualize(facilities, boundaries, accessibility)

            # STEP 6: Save outputs
            self.save_outputs(boundaries, facilities, accessibility, stats)

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
            raise