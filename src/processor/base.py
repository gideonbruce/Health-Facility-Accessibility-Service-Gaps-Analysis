from abc import ABC, abstractmethod
from logger import Logger
import geopandas as gpd

from src.config import Config

class BaseProcessor(ABC):
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def process(self, data):
        """Process data"""
        pass