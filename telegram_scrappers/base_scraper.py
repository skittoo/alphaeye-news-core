from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseTelegramScraper(ABC):
    """
    Abstract base class for Telegram channel scrapers.
    All specific channel scrapers should inherit from this class.
    """
    
    def __init__(self, channel_id: str, channel_name: str, **kwargs):
        """
        Initialize the scraper with channel details.
        
        Args:
            channel_id: The unique identifier for the Telegram channel
            channel_name: The name of the Telegram channel
            **kwargs: Additional channel-specific configuration parameters
        """
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.config = kwargs
    
    @abstractmethod
    async def connect(self, client) -> bool:
        """
        Connect to the Telegram channel.
        
        Args:
            client: The Telegram client instance
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def scrape(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape messages from the channel.
        
        Args:
            limit: Optional limit on the number of messages to scrape
            
        Returns:
            List of scraped messages as dictionaries
        """
        pass
    
    @abstractmethod
    async def process_message(self, message) -> Dict[str, Any]:
        """
        Process a single message from the channel.
        
        Args:
            message: The raw message object from Telegram
            
        Returns:
            Processed message as a dictionary
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this scraper.
        
        Returns:
            Dictionary with scraper metadata
        """
        return {
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "config": self.config
        } 