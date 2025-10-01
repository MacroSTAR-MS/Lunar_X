import logging
import sys
from typing import Dict, Any, List, Optional

def title() -> str:
    return r'''# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  _                                       __  __
# | |      _   _   _ __     __ _   _ __    \ \/ /
# | |     | | | | | '_ \   / _` | | '__|    \  / 
# | |___  | |_| | | | | | | (_| | | |       /  \ 
# |_____|  \__,_| |_| |_|  \__,_| |_|      /_/\_\ (Beta|MacroSTAR)              
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''

class ColorCodes:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    SUCCESS = "\033[92m"

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')

class EmojiFormatter(logging.Formatter):
    _log_level_colors = {
        logging.DEBUG: ColorCodes.BRIGHT_BLUE,
        logging.INFO: ColorCodes.BRIGHT_CYAN,
        logging.WARNING: ColorCodes.BRIGHT_YELLOW,
        logging.ERROR: ColorCodes.BRIGHT_RED,
        logging.CRITICAL: ColorCodes.RED + ColorCodes.BOLD,
        SUCCESS_LEVEL: ColorCodes.BRIGHT_GREEN,
    }

    _log_level_emojis = {
        logging.DEBUG: "🐛",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
        SUCCESS_LEVEL: "✅", 
    }

    def format(self, record):
        record.emoji_prefix = self._log_level_emojis.get(record.levelno, "")
        
        color = self._log_level_colors.get(record.levelno, ColorCodes.RESET)
        record.colored_levelname = f"{color}{record.levelname}{ColorCodes.RESET}"
        if record.name == 'LunarBot':
            record.logger_display = ''
        elif record.name == 'LunarPlugins':
            record.logger_display = '[Lunar Plugins System]'
        elif record.name.startswith('Plugins:'):
            record.logger_display = f'[Lunar Plugins System] [{record.name}]'
        else:
            record.logger_display = f'[{record.name}]'
        formatted_message = super().format(record)
        return formatted_message

class LunarLogger:
    def __init__(self):
        self._loggers = {}
        self._setup_default_loggers()
    
    def _setup_default_loggers(self):
        self._setup_logger(
            'LunarBot',
            '[%(asctime)s.%(msecs)03d] %(emoji_prefix)s %(colored_levelname)s %(message)s',
            'INFO'
        )
        self._setup_logger(
            'LunarPlugins',
            '[%(asctime)s.%(msecs)03d] %(logger_display)s %(emoji_prefix)s %(colored_levelname)s %(message)s',
            'INFO'
        )
    
    def _setup_logger(self, name: str, format_str: str, level: str):
        logger = logging.getLogger(name)
        
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        handler = logging.StreamHandler(sys.stdout)
        
        handler.setFormatter(EmojiFormatter(
            format_str,
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        logger.addHandler(handler)
        logger.propagate = False
        
        self._loggers[name] = logger
    
    def configure_from_config(self, config: Dict[str, Any]):
        log_level = config.get('log_level', 'INFO')
        
        for logger_name in self._loggers:
            self.set_level(logger_name, log_level)
    
    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            default_format = '[%(asctime)s.%(msecs)03d] %(logger_display)s %(emoji_prefix)s %(colored_levelname)s %(message)s'
            self._setup_logger(name, default_format, 'INFO')
        
        return self._loggers[name]
    
    def set_level(self, logger_name: str, level: str):
        if logger_name in self._loggers:
            log_level = getattr(logging, level.upper(), logging.INFO)
            self._loggers[logger_name].setLevel(log_level)
    
    def info(self, message: str, logger_name: str = 'LunarBot'):
        self.get_logger(logger_name).info(message)
    
    def error(self, message: str, logger_name: str = 'LunarBot'):
        self.get_logger(logger_name).error(message)
    
    def warning(self, message: str, logger_name: str = 'LunarBot'):
        self.get_logger(logger_name).warning(message)
    
    def debug(self, message: str, logger_name: str = 'LunarBot'):
        self.get_logger(logger_name).debug(message)
    
    def critical(self, message: str, logger_name: str = 'LunarBot'):
        self.get_logger(logger_name).critical(message)

    def success(self, message: str, logger_name: str = 'LunarBot'): 
        self.get_logger(logger_name).log(SUCCESS_LEVEL, message)

logger = LunarLogger()
