"""
AlphaEye Telegram Scraper Package

This package provides a flexible and extensible framework for scraping content
from Telegram channels with different processing logic for each channel.
"""

__version__ = "0.1.0"

from .base_scraper import BaseTelegramScraper
from .scraper_factory import TelegramScraperFactory
from .scraper_manager import TelegramScraperManager

# Import channel-specific scrapers for easy access
try:
    from .channels.basic_text_channel import BasicTextChannelScraper
except ImportError:
    pass

__all__ = [
    'BaseTelegramScraper',
    'TelegramScraperFactory',
    'TelegramScraperManager',
    'BasicTextChannelScraper',
]
