import logging

gs_logger = logging.getLogger("geoservercloud")
# Prevent "No handler found" warnings if the application doesn't configure logging
gs_logger.addHandler(logging.NullHandler())
