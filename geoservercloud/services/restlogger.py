import logging

time_formatter = logging.Formatter(
    "{asctime} - {name}:{levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(time_formatter)
gs_logger = logging.getLogger("GS Session")
gs_logger.setLevel(logging.INFO)
gs_logger.addHandler(stream_handler)
