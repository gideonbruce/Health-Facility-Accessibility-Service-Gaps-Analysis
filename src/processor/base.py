from abc import ABC, abstractmethod
import geopandas as gpd

from src.logger import Logger
from src.config import Config

class BaseProcessor(ABC):
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def process(self, data):
        """Process data"""
        pass