import copy
import sys
from aiologger import Logger
from aiologger.levels import LogLevel

from aiologger.formatters.base import Formatter


from app.utils.module_loading import import_string
from app.core.config import settings


def setup_handlers(logging_config, setup_name: str = "handlers", **kwargs):
    
    handlers = []
    for handler in kwargs.values():

        handler_class = import_string(handler.pop("class"))

        formatter = handler.pop("formatter")
        filters = handler.pop("filters", [])
        level = handler.pop("level", LogLevel.NOTSET)

        handler_instance = handler_class(**handler)
        handler_instance.level = level

        if formatter:
            handler_instance.formatter = logging_config["formatters"][formatter]
        
        for filter_name in filters:
            handler_instance.add_filter(logging_config["filters"][filter_name])
            
        handlers.append(handler_instance)

    logging_config[setup_name] = handlers
    

def setup_formatters(logging_config, setup_name: str = "formatters", **kwargs):
    formatters = {}
    for name, config in kwargs.items():
        fmt = config.get('format')
        datefmt = config.get('datefmt')
        formatters[name] = Formatter(fmt=fmt, datefmt=datefmt)
    
    logging_config[setup_name] = formatters


def setup_filters(logging_config, setup_name: str = "filters", **kwargs):

    filters: dict = {}

    for name, class_name in kwargs.items():
        setup_class = import_string(class_name)
        filters[name] = setup_class()

    logging_config[setup_name] = filters


def get_logger(name: str) -> Logger:

    PROXY_LOGGER = Logger(name=name)

    logging_config: dict = dict()

    config_copy = copy.deepcopy(settings.LOGGING)
    
    for config, value in config_copy.items():
        setup_class = getattr(sys.modules[__name__], f"setup_{config}", None)
        if setup_class and callable(setup_class):
            setup_class(logging_config, **value)
    
    for handler in logging_config["handlers"]:
        PROXY_LOGGER.add_handler(handler)

    return PROXY_LOGGER
