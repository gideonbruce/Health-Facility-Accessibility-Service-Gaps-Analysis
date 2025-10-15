import logging
import sys
from pathlib import Path

class Logger:
    """Centralized logging configuration"""
    
    _loggers = {}
    
    @staticmethod
    def setup(log_dir: str = "logs", level: int = logging.INFO) -> None:
        """Configure logging for the application"""
        Path(log_dir).mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        fh = logging.FileHandler(f"{log_dir}/pipeline.log")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        
        # Stream handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(level)
        sh.setFormatter(formatter)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(fh)
        root_logger.addHandler(sh)
    
    @staticmethod
    def get(name: str) -> logging.Logger:
        """Get or create logger"""
        if name not in Logger._loggers:
            Logger._loggers[name] = logging.getLogger(name)
        return Logger._loggers[name]