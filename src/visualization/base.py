from abc import ABC, abstractmethod
from pathlib import Path
from logger import Logger
from src.config import Config

class BaseVisualizer(ABC):
    """Abstract base class for visualizations"""
    
    def __init__(self, config: Config, output_dir: str):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """Generate visualization"""
        pass