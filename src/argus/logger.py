"""
Argus Logging System
Configures Loguru logger with structured formats and optional stdout fallback.
"""

import sys

try:
    from loguru import logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
except ImportError:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    )
    logger = logging.getLogger("argus")
    logger.success = logger.info
