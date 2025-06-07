import asyncio
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from .scraper_factory import TelegramScraperFactory
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class TelegramScraperManager:
    """
    Manager class that handles the execution and coordination of multiple telegram scrapers.
    This class provides a high-level interface for working with the scrapers.
    """
    
    def __init__(self, api_id: str, api_hash: str, session_name: str = "telegram_scraper"):
        """
        Initialize the scraper manager.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_name: Name for the Telegram session
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        self.logger = self._setup_logger()
        
        # Auto-discover available scrapers
        self.discovered_scrapers = TelegramScraperFactory.auto_discover_scrapers()
        self.logger.info(f"Discovered scrapers: {self.discovered_scrapers}")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up and configure logger"""
        logger = logging.getLogger("TelegramScraperManager")
        logger.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(ch)
        
        return logger
    
    async def initialize(self) -> bool:
        """
        Initialize the Telegram client.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import telethon only when needed
            try:
                from telethon import TelegramClient
            except ImportError:
                self.logger.error("Telethon library not found. Please install it with 'pip install telethon'")
                return False
            
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start()
            self.logger.info(f"Telegram client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram client: {e}")
            return False
    
    async def add_channel(self, channel_name: str, scraper_type: str, **kwargs) -> bool:
        """
        Add a new channel to be scraped.
        
        Args:
            channel_name: Unique name for the channel
            scraper_type: Type of scraper to use (must be registered)
            **kwargs: Additional configuration for the scraper
            
        Returns:
            True if channel was added successfully, False otherwise
        """
        try:
            # Extract channel_id from kwargs to avoid duplicate parameter
            channel_id = kwargs.pop('channel_id', channel_name)
            
            # Get the scraper
            scraper = TelegramScraperFactory.get_scraper(scraper_type, 
                                                         channel_id=channel_id,
                                                         channel_name=channel_name,
                                                         **kwargs)
            
            # Connect the scraper to the channel
            if self.client:
                await scraper.connect(self.client)
                self.logger.info(f"Added channel: {channel_name} using {scraper_type} scraper")
                return True
            else:
                self.logger.error("Client not initialized. Call initialize() first")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add channel {channel_name}: {e}")
            return False
    
    async def scrape_channel(self, channel_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape messages from a specific channel.
        
        Args:
            channel_name: The name of the channel to scrape
            limit: Maximum number of messages to scrape
            
        Returns:
            List of scraped messages
        """
        try:
            # Get the scraper instance
            scraper = TelegramScraperFactory.get_scraper(channel_name)
            
            # Ensure the scraper is connected
            if not scraper.client and self.client:
                await scraper.connect(self.client)
            
            # Scrape the channel
            results = await scraper.scrape(limit=limit)
            self.logger.info(f"Scraped {len(results)} messages from {channel_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to scrape channel {channel_name}: {e}")
            return []
    
    async def scrape_all_channels(self, limit: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape messages from all registered channels.
        
        Args:
            limit: Maximum number of messages to scrape from each channel
            
        Returns:
            Dictionary mapping channel names to lists of scraped messages
        """
        results = {}
        scrapers = TelegramScraperFactory.get_all_scrapers()
        
        for scraper in scrapers:
            channel_name = scraper.channel_name
            try:
                # Ensure the scraper is connected
                if not scraper.client and self.client:
                    await scraper.connect(self.client)
                
                # Scrape the channel
                channel_results = await scraper.scrape(limit=limit)
                results[channel_name] = channel_results
                self.logger.info(f"Scraped {len(channel_results)} messages from {channel_name}")
                
            except Exception as e:
                self.logger.error(f"Error scraping channel {channel_name}: {e}")
                results[channel_name] = []
        
        return results
    
    def get_registered_channels(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered channels.
        
        Returns:
            List of dictionaries with channel information
        """
        scrapers = TelegramScraperFactory.get_all_scrapers()
        return [scraper.get_info() for scraper in scrapers]
    
    async def remove_channel(self, channel_name: str) -> bool:
        """
        Remove a channel from the scraper.
        
        Args:
            channel_name: The name of the channel to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        return TelegramScraperFactory.remove_scraper(channel_name)
    
    async def close(self) -> None:
        """
        Close the Telegram client and release resources.
        """
        if self.client:
            await self.client.disconnect()
            self.logger.info("Telegram client disconnected")

    def save_to_json(self, data: Dict[str, List[Dict[str, Any]]], filename: str = None) -> str:
        """
        Save scraped messages to a JSON file in the data folder.
        
        Args:
            data: Dictionary mapping channel names to lists of scraped messages
            filename: Optional custom filename. If not provided, generates timestamp-based name
            
        Returns:
            Path to the saved file
        """
        # Create data folder if it doesn't exist
        data_folder = Path("data")
        data_folder.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telegram_messages_{timestamp}.json"
        
        # Ensure filename ends with .json
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Full path to the file
        file_path = data_folder / filename
        
        # Prepare metadata
        save_data = {
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "total_channels": len(data),
                "total_messages": sum(len(messages) for messages in data.values()),
                "channels": list(data.keys())
            },
            "data": data
        }
        
        # Save to JSON file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully saved {save_data['metadata']['total_messages']} messages to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save data to {file_path}: {e}")
            raise


# Usage example
async def main():
    # Create a scraper manager
    manager = TelegramScraperManager(
        api_id=os.getenv("API_ID"),
        api_hash=os.getenv("API_HASH"),
        session_name="alphaeye_scraper"
    )
    
    # Initialize the client
    await manager.initialize()
    
    # Add channels with specific channel IDs
    await manager.add_channel(
        channel_name="AjaNews",
        scraper_type="AjaNews_channel", 
        channel_id="@AjaNews",  # Use username instead of numeric ID
    )
    
    # You can add more channels like this:
    # await manager.add_channel(
    #     channel_name="TechNews", 
    #     scraper_type="AjaNews_channel",
    #     channel_id="@technews_channel",  # Replace with actual channel
    #     categories=["technology", "ai"]
    # )
    
    # Scrape all channels
    results = await manager.scrape_all_channels(limit=1)
    
    # Save results to JSON file
    saved_file = manager.save_to_json(results)
    print(f"Results saved to: {saved_file}")
    
    print(results)
    
    # Process the results
    for channel_name, messages in results.items():
        print(f"Channel: {channel_name}")
        print(f"Messages scraped: {len(messages)}")
        for msg in messages[:3]:  # Print first 3 messages as a sample
            print(f"- [{msg['date']}] {msg['text'][:100]}...")
        print()
    
    # Close the manager
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main()) 