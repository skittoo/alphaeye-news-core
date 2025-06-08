from typing import Dict, List, Any, Optional
import datetime
from ..base_scraper import BaseTelegramScraper
from ..data_manager import MongoDataManager


class BasicTextChannelScraper(BaseTelegramScraper):
    """
    Scraper for a generic news channel.
    This is a sample implementation showing how to extend the base scraper.
    """
    
    def __init__(self, channel_id: str, channel_name: str, **kwargs):
        """
        Initialize the news channel scraper.
        
        Args:
            channel_id: The channel ID or username
            channel_name: The channel name
            **kwargs: Additional configuration options
                - keywords: List of keywords to filter messages
                - categories: List of news categories to track
                - save_to_mongo: Whether to save messages to MongoDB (default: True)
        """
        super().__init__(channel_id, channel_name, **kwargs)
        
        # Custom parameters for this specific scraper
        self.keywords = kwargs.get('keywords', [])
        self.categories = kwargs.get('categories', [])
        self.client = None
        
        # MongoDB integration
        self.save_to_mongo = kwargs.get('save_to_mongo', True)
        self.data_manager = MongoDataManager() if self.save_to_mongo else None
    
    async def connect(self, client) -> bool:
        """
        Connect to the Telegram channel and MongoDB.
        
        Args:
            client: The Telegram client instance
            
        Returns:
            True if connection was successful
        """
        try:
            self.client = client
            # Verify the channel exists and is accessible
            channel = await client.get_entity(self.channel_id)
            
            # Connect to MongoDB if enabled
            if self.data_manager:
                mongo_connected = await self.data_manager.connect()
                if mongo_connected:
                    print(f"✅ Connected to MongoDB for channel {self.channel_name}")
                else:
                    print(f"⚠️  Failed to connect to MongoDB for channel {self.channel_name}")
            
            return True
        except Exception as e:
            print(f"Error connecting to channel {self.channel_id}: {e}")
            return False
    
    async def scrape(self, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """
        Scrape messages from the news channel and save to MongoDB.
        Only scrapes messages newer than the latest message already stored in MongoDB.
        
        Args:
            limit: Maximum number of messages to scrape for initial/full scrapes.
                   For incremental scrapes (when latest_message_id exists), 
                   all new messages will be scraped regardless of limit.
            
        Returns:
            List of processed message dictionaries
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first")
            
        try:
            # Get the latest message ID from MongoDB to avoid duplicates
            latest_message_id = None
            is_incremental_scrape = False
            
            if self.data_manager:
                latest_message_id = await self.data_manager.get_latest_message_id(self.channel_name)
                if latest_message_id:
                    is_incremental_scrape = True
                    print(f"🔍 Starting incremental scraping from message ID {latest_message_id + 1} for channel {self.channel_name}")
                    print(f"📝 Will scrape ALL new messages (ignoring limit for incremental scrape)")
                else:
                    print(f"🔍 No previous messages found for channel {self.channel_name}, starting fresh scrape with limit {limit}")
            
            messages = []
            
            # Configure iteration parameters
            iter_kwargs = {}
            
            if is_incremental_scrape:
                # For incremental scraping, get ALL new messages (no limit)
                iter_kwargs['min_id'] = latest_message_id
                print(f"🚀 Incremental scrape: fetching all messages after ID {latest_message_id}")
            else:
                # For initial/full scraping, respect the limit
                iter_kwargs['limit'] = limit
                print(f"🚀 Initial scrape: fetching up to {limit} messages")
            
            message_count = 0
            async for message in self.client.iter_messages(self.channel_id, **iter_kwargs):
                message_count += 1
                print("--------------------------------")
                print(f"Processing message {message_count}: ID {message.id}")
                if message.text:
                    print(f"Text preview: {message.text[:100]}{'...' if len(message.text) > 100 else ''}")
                else:
                    print("No text content")
                print("--------------------------------")

                # Skip messages without text
                if not message.text:
                    continue
                    
                # Process the message
                processed = await self.process_message(message)
                if processed:  # Only add non-empty results
                    messages.append(processed)
                    
                    # Save to MongoDB immediately if enabled
                    if self.data_manager:
                        await self.data_manager.save_message(processed)
            
            # Log results with more detail
            if is_incremental_scrape:
                print(f"📊 Incremental scrape completed: {len(messages)} new messages from {self.channel_name}")
                print(f"🆕 All messages after ID {latest_message_id} have been processed")
            else:
                print(f"📊 Initial scrape completed: {len(messages)} messages from {self.channel_name}")
                
            if self.data_manager:
                total_count = await self.data_manager.get_message_count(self.channel_name)
                print(f"📚 Total messages in MongoDB for {self.channel_name}: {total_count}")
                
            if len(messages) == 0:
                print(f"ℹ️  No new messages found for {self.channel_name}")
            else:
                print(f"✅ Successfully processed {len(messages)} messages from {self.channel_name}")
                    
            return messages
        except Exception as e:
            print(f"❌ Error scraping messages from {self.channel_id}: {e}")
            return []
    
    async def process_message(self, message) -> Dict[str, Any]:
        """
        Process a single message from the news channel.
        
        Args:
            message: The raw message object from Telegram
            
        Returns:
            Processed message as a dictionary
        """

        result = {
            "id": message.id,
            "date": message.date.isoformat(),
            "text": message.text,
            "channel": self.channel_name,
            "has_media": bool(message.media),
            "processed_at": datetime.datetime.now().isoformat(),
        }
                
        
        return result
    
    def _categorize_news(self, text: str) -> List[str]:
        """
        Categorize news based on text content.
        This is a simple example - in a real implementation,
        you might use NLP or a more sophisticated approach.
        
        Args:
            text: The message text
            
        Returns:
            List of detected categories
        """
        pass