from abc import ABC, abstractmethod
from src.config import Config
from src.logger import Logger

#abstract base class for analysis modules
class BaseAnalyzer(ABC):
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self, *args, **kwargs):
        #performing analysis
        pass