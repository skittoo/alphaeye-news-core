from typing import Dict, Type, List, Optional, Any
import importlib
import os
import inspect
from pathlib import Path

from .base_scraper import BaseTelegramScraper


class TelegramScraperFactory:
    """
    Factory class for creating and managing Telegram channel scrapers.
    """
    
    _scrapers: Dict[str, Type[BaseTelegramScraper]] = {}
    _instances: Dict[str, BaseTelegramScraper] = {}
    
    @classmethod
    def register_scraper(cls, channel_name: str, scraper_class: Type[BaseTelegramScraper]) -> None:
        """
        Register a new scraper class.
        
        Args:
            channel_name: Unique name for the channel scraper
            scraper_class: The scraper class (must inherit from BaseTelegramScraper)
        """
        if not issubclass(scraper_class, BaseTelegramScraper):
            raise TypeError(f"Scraper class must inherit from BaseTelegramScraper")
        
        cls._scrapers[channel_name] = scraper_class
    
    @classmethod
    def get_scraper(cls, scraper_type: str, **kwargs) -> BaseTelegramScraper:
        """
        Get an instance of a scraper for a specific channel.
        
        Args:
            scraper_type: The type/name of the scraper to get
            **kwargs: Additional configuration for the scraper
            
        Returns:
            An instance of the appropriate scraper
            
        Raises:
            KeyError: If no scraper is registered for the given scraper type
        """
        if scraper_type not in cls._scrapers:
            raise KeyError(f"No scraper registered for scraper type: {scraper_type}")
        
        # Create a new instance if one doesn't exist or if new configs are provided
        if scraper_type not in cls._instances or kwargs:
            # Extract channel_id and channel_name from kwargs to avoid duplicate parameter
            channel_id = kwargs.pop('channel_id', scraper_type)
            actual_channel_name = kwargs.pop('channel_name', scraper_type)
            
            cls._instances[scraper_type] = cls._scrapers[scraper_type](
                channel_id=channel_id,
                channel_name=actual_channel_name,
                **kwargs
            )
            
        return cls._instances[scraper_type]
    
    @classmethod
    def get_all_scrapers(cls) -> List[BaseTelegramScraper]:
        """
        Get all registered scraper instances.
        
        Returns:
            List of all scraper instances
        """
        return list(cls._instances.values())
    
    @classmethod
    def list_available_scrapers(cls) -> List[str]:
        """
        List all registered scraper types.
        
        Returns:
            List of scraper names
        """
        return list(cls._scrapers.keys())
    
    @classmethod
    def remove_scraper(cls, channel_name: str) -> bool:
        """
        Remove a scraper from the factory.
        
        Args:
            channel_name: The name of the channel scraper to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if channel_name in cls._instances:
            del cls._instances[channel_name]
        
        if channel_name in cls._scrapers:
            del cls._scrapers[channel_name]
            return True
        return False
    
    @classmethod
    def auto_discover_scrapers(cls) -> List[str]:
        """
        Automatically discover and register all scraper classes in the scrapers directory.
        
        Returns:
            List of discovered scraper names
        """
        discovered = []
        scrapers_dir = Path(__file__).parent / "channels"
        
        if not scrapers_dir.exists():
            return discovered
        
        # Find all potential scraper modules
        for file_path in scrapers_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
                
            module_name = file_path.stem
            module_path = f"telegram_scrappers.channels.{module_name}"
            
            try:
                module = importlib.import_module(module_path)
                
                # Find all classes in the module that inherit from BaseTelegramScraper
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTelegramScraper) and 
                        obj is not BaseTelegramScraper):
                        
                        # Register the scraper with the module name as the key
                        cls.register_scraper(module_name, obj)
                        discovered.append(module_name)
                        
            except (ImportError, AttributeError) as e:
                print(f"Error loading scraper module {module_name}: {e}")
                
        return discovered 