import logging
import sys


console_handler = logging.StreamHandler(stream=sys.stdout)
console_formatter = logging.Formatter(
			"%(asctime)s [%(levelname)s]:%(message)s ",
			"%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(console_formatter)


__all__ = ('console_handler')

