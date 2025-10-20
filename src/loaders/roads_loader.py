import geopandas as gpd
import osmnx as ox
from pathlib import Path

class RoadsLoader:
    """
    Loader for road network data.
    - Uses local HOTOSM shapefiles or geopackage if available.
    - Falls back to OSMnx download if no local file is configured.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path(config["data_dir"]) / "Roads"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = config.get("logger", None)

        # Local road file path (GPKG or SHP)
        self.local_path = config.get("roads", {}).get("local_file")
        self.output_file = self.data_dir / "roads.geojson"

    def log(self, message: str):
        if self.logger:
            self.logger.info(message)
        else:
            print(message)

    def load(self) -> gpd.GeoDataFrame:
        """Load roads from local file or download if not provided"""
        if self.local_path and Path(self.local_path).exists():
            self.log(f" Loading roads from local file: {self.local_path}")
            return self._load_local()

        # Fallback to cached GeoJSON
        if self.output_file.exists():
            self.log(f" Loading cached roads from {self.output_file}")
            return gpd.read_file(self.output_file)

        # Fallback to OSMnx download
        self.log(" No local or cached road data found. Downloading road network...")
        roads = self._download()
        roads.to_file(self.output_file, driver="GeoJSON")
        self.log(f" Roads saved to {self.output_file}")
        return roads

    def _load_local(self) -> gpd.GeoDataFrame:
        """Load from local GPKG or SHP"""
        file_path = Path(self.local_path)
        if file_path.suffix.lower() == ".gpkg":
            gdf = gpd.read_file(file_path, layer=0)
        else:
            gdf = gpd.read_file(file_path)

        self.log(f" Loaded {len(gdf)} road segments from {file_path.name}")
        return gdf

    def _download(self) -> gpd.GeoDataFrame:
        """Download roads via OSMnx if no local file"""
        place_name = self.config.get("roads", {}).get("place_name")
        boundary_file = self.config.get("roads", {}).get("boundary_file")

        if place_name:
            self.log(f" Downloading roads for place: {place_name}")
            G = ox.graph_from_place(place_name, network_type="drive")
        elif boundary_file and Path(boundary_file).exists():
            self.log(f" Downloading roads within boundary: {boundary_file}")
            boundary_gdf = gpd.read_file(boundary_file)
            polygon = boundary_gdf.unary_union
            G = ox.graph_from_polygon(polygon, network_type="drive")
        else:
            raise ValueError(
                "No valid roads['local_file'], roads['place_name'], or roads['boundary_file'] provided."
            )

        roads_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)
        return roads_gdf
