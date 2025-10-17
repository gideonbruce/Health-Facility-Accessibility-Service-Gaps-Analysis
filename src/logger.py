import codecs
import logging
import sys
from pathlib import Path

class Logger:
    
    _loggers = {}
    
    @staticmethod
    def setup(log_dir: str = "logs", level: int = logging.INFO) -> None:
        Path(log_dir).mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        #file handler
        fh = logging.FileHandler(f"{log_dir}/pipeline.log", encoding='utf-8')
        fh.setLevel(level)
        fh.setFormatter(formatter)
        
        #stream handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(level)
        sh.setFormatter(formatter)

        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding='utf-8')
        else:
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        
        #root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(fh)
        root_logger.addHandler(sh)
    
    @staticmethod
    def get(name: str) -> logging.Logger:
        if name not in Logger._loggers:
            Logger._loggers[name] = logging.getLogger(name)
        return Logger._loggers[name]