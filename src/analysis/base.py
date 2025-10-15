
from abc import ABC, abstractmethod
from logging import Logger

from config import Config

class BaseAnalyzer(ABC):
    """Abstract base class for analysis modules"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self, *args, **kwargs):
        """Perform analysis"""
        pass