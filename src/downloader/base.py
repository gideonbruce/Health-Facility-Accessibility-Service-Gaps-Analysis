from abc import ABC, abstractmethod
from src.logger import Logger
from pathlib import Path

class BaseDownloader(ABC):
    """Abstract base class for all downloaders"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = Logger.get(self.__class__.__name__)
    
    @abstractmethod
    def download(self) -> str:
        """Download data and return path"""
        pass
