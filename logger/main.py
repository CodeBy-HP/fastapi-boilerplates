
from .logger import setup_logger, get_logger, LoggerConfig
from contextlib import asynccontextmanager



# Initialize the logger
logger_config = LoggerConfig(
    logger_name="app",
    log_level=LOG_LEVEL,
    log_dir=LOG_DIR,
    log_to_console=LOG_TO_CONSOLE,
    log_to_file=LOG_TO_FILE,
    use_colors=LOG_USE_COLORS,
)
setup_logger(logger_config)

# Get logger instance for this module
logger = get_logger("main")
