from abc import ABC, abstractmethod
from logging import Logger
import geopandas as gpd

from config import Config

class BaseProcessor(ABC):
    """Abstract base class for data processors"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def process(self, data):
        """Process data"""
        pass