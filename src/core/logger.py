import logging
import logging.config
import os
from .configs import settings

os.makedirs("logs", exist_ok=True)

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))


# Configure the logger
logger = logging.getLogger("mdo_service")
logger.setLevel(settings.LOG_LEVEL)
