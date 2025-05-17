import structlog

# 1. Configure structlog for loggers obtained via structlog.get_logger()
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,  # Filter based on stdlib log levels
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(), # Render stack info for errors
        structlog.processors.format_exc_info,   # Render exception info
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),    # Render as JSON
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 2. Define LOGGING_CONFIG for Uvicorn (and standard library logging)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Keep existing loggers (like uvicorn's)
    "formatters": {
        "json_formatter": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(), # Final rendering step
            "foreign_pre_chain": [ # Processors for stdlib log records
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.format_exc_info,
            ],
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
            "stream": "ext://sys.stdout", # Or sys.stderr
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False, # Avoid duplicate logging if child loggers are also configured
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# 3. Get a structlog logger for this module
log = structlog.get_logger(__name__)