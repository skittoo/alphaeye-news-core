import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()


class MongoDataManager:
    """
    Simple MongoDB data manager for Telegram scrapers.
    Handles connection and data insertion to a single collection.
    """
    
    def __init__(self, collection_name: str = "telegram_messages"):
        """
        Initialize MongoDB data manager.
        
        Args:
            collection_name: Name of the MongoDB collection to use
        """
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.logger = self._setup_logger()
        
        # MongoDB connection settings from environment
        self.host = os.getenv("MONGO_HOST", "localhost")
        self.port = int(os.getenv("MONGO_PORT", 27017))
        self.username = os.getenv("MONGO_USERNAME")
        self.password = os.getenv("MONGO_PASSWORD")
        self.database_name = os.getenv("MONGO_DATABASE", "alphaeye_news")
        self.auth_db = os.getenv("MONGO_AUTH_DB", "admin")
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the data manager."""
        logger = logging.getLogger(f"MongoDataManager.{self.collection_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            
        return logger
    
    async def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create MongoDB client
            if self.username and self.password:
                self.client = MongoClient(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    authSource=self.auth_db
                )
                self.logger.info(f"Connecting to MongoDB at {self.host}:{self.port} with authentication")
            else:
                self.client = MongoClient(self.host, self.port)
                self.logger.info(f"Connecting to MongoDB at {self.host}:{self.port} without authentication")
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            self.logger.info(f"Successfully connected to MongoDB database '{self.database_name}', collection '{self.collection_name}'")
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    async def save_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Save a single message to MongoDB.
        
        Args:
            message_data: Dictionary containing message data
            
        Returns:
            True if save successful, False otherwise
        """
        if self.collection is None:
            self.logger.error("Not connected to MongoDB. Call connect() first.")
            return False
            
        try:
            # Check if message already exists (by ID and channel)
            message_id = message_data.get('id')
            channel_name = message_data.get('channel')
            
            if message_id is not None:
                query = {'id': message_id}
                if channel_name:
                    query['channel'] = channel_name
                
                existing_message = self.collection.find_one(query)
                if existing_message:
                    self.logger.info(f"Message already exists - ID: {message_id}, Channel: {channel_name or 'unknown'}")
                    return True  # Not an error, just already exists
            
            # Add timestamp for when data was inserted
            message_data['inserted_at'] = datetime.now().isoformat()
            
            # Insert the document
            result = self.collection.insert_one(message_data)
            
            self.logger.debug(f"Saved message with ID: {result.inserted_id}")
            return True
            
        except DuplicateKeyError:
            self.logger.warning(f"Message already exists (duplicate key): {message_data.get('id', 'unknown')}")
            return True  # Not an error, just already exists
        except Exception as e:
            self.logger.error(f"Error saving message to MongoDB: {e}")
            return False
    
    async def save_messages(self, messages_data: List[Dict[str, Any]]) -> int:
        """
        Save multiple messages to MongoDB.
        
        Args:
            messages_data: List of message dictionaries
            
        Returns:
            Number of messages successfully saved
        """
        if self.collection is None:
            self.logger.error("Not connected to MongoDB. Call connect() first.")
            return 0
            
        if not messages_data:
            self.logger.info("No messages to save")
            return 0
            
        try:
            # Add timestamp for when data was inserted
            current_time = datetime.now().isoformat()
            for message in messages_data:
                message['inserted_at'] = current_time
            
            # Insert all documents
            result = self.collection.insert_many(messages_data, ordered=False)
            
            saved_count = len(result.inserted_ids)
            self.logger.info(f"Successfully saved {saved_count} messages to MongoDB")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Error saving messages to MongoDB: {e}")
            # Try to save individually to see how many we can save
            saved_count = 0
            for message in messages_data:
                if await self.save_message(message):
                    saved_count += 1
            return saved_count
    
    async def get_message_count(self, channel_name: Optional[str] = None) -> int:
        """
        Get count of messages in the collection.
        
        Args:
            channel_name: Optional filter by channel name
            
        Returns:
            Number of messages in collection
        """
        if self.collection is None:
            return 0
            
        try:
            if channel_name:
                filter_query = {"channel": channel_name}
            else:
                filter_query = {}
                
            count = self.collection.count_documents(filter_query)
            return count
        except Exception as e:
            self.logger.error(f"Error getting message count: {e}")
            return 0
    
    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed") 