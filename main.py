
if __name__ == "__main__":
    from src.config import Config
    from src.logger import Logger
    from src.pipeline import Pipeline
    
    #setup
    Logger.setup(log_dir="logs")
    config = Config("config/config.yaml")
    
    #run
    pipeline = Pipeline(config)
    results = pipeline.run()
