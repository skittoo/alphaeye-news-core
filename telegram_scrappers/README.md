# AlphaEye Telegram Scraper

A flexible and extensible framework for scraping content from Telegram channels with different processing logic for each channel.

## Features

- 🔌 **Plug-and-Play Architecture**: Easily add new channel scrapers with custom logic
- 🔄 **Auto-Discovery**: Automatically discovers and registers new scrapers
- 🧩 **Strategy Pattern**: Different scraping strategies for different channel types
- 🏭 **Factory Design**: Centralized scraper creation and management
- 📊 **Customizable Processing**: Process messages according to channel-specific needs

## Installation

### Requirements

- Python 3.7+
- Telethon library for Telegram API access

```bash
pip install telethon
```

## Usage

### Basic Usage

```python
import asyncio
from telegram_scrappers import TelegramScraperManager

async def main():
    # Create a scraper manager
    manager = TelegramScraperManager(
        api_id="YOUR_API_ID",  # Get from https://my.telegram.org/apps
        api_hash="YOUR_API_HASH",
        session_name="alphaeye_scraper"
    )
    
    # Initialize the client
    await manager.initialize()
    
    # Add channels to scrape
    await manager.add_channel(
        channel_name="crypto_news",        # Your internal name for the channel
        scraper_type="crypto_channel",     # Type of scraper to use
        channel_id="@cryptonews",          # Actual Telegram channel username
        tracked_coins=["BTC", "ETH"],      # Channel-specific parameters
        extract_prices=True,
        ignore_memes=True
    )
    
    # Scrape a specific channel
    messages = await manager.scrape_channel("crypto_news", limit=50)
    
    # Process the messages
    for msg in messages:
        print(f"[{msg['date']}] {msg['text'][:100]}...")
    
    # Close the manager
    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Creating a Custom Channel Scraper

Create a new file in the `channels` directory:

```python
# telegram_scrappers/channels/my_custom_channel.py
from typing import Dict, List, Any, Optional
from ..base_scraper import BaseTelegramScraper

class MyCustomChannelScraper(BaseTelegramScraper):
    """
    Custom scraper for a specific channel type.
    """
    
    def __init__(self, channel_id: str, channel_name: str, **kwargs):
        super().__init__(channel_id, channel_name, **kwargs)
        
        # Add custom parameters
        self.custom_param = kwargs.get('custom_param', 'default_value')
        self.client = None
    
    async def connect(self, client) -> bool:
        self.client = client
        try:
            channel = await client.get_entity(self.channel_id)
            return True
        except Exception as e:
            print(f"Error connecting to channel {self.channel_id}: {e}")
            return False
    
    async def scrape(self, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        # Implement your custom scraping logic
        messages = []
        async for message in self.client.iter_messages(self.channel_id, limit=limit):
            processed = await self.process_message(message)
            if processed:
                messages.append(processed)
        return messages
    
    async def process_message(self, message) -> Dict[str, Any]:
        # Implement your custom message processing logic
        result = {
            "id": message.id,
            "date": message.date.isoformat(),
            "text": message.text,
            "channel": self.channel_name,
            # Add custom processing fields
            "custom_field": self._custom_processing(message.text)
        }
        return result
    
    def _custom_processing(self, text: str) -> str:
        # Your custom processing logic
        return text.upper()  # Example: convert text to uppercase
```

### Architecture

The Telegram scraper is built using several design patterns:

1. **Strategy Pattern**: Each channel scraper implements a common interface (`BaseTelegramScraper`) but can have different processing logic.

2. **Factory Pattern**: The `TelegramScraperFactory` handles creation and management of scrapers.

3. **Facade Pattern**: The `TelegramScraperManager` provides a simplified interface for using the scraper system.

## Adding a New Channel

To add a new channel type:

1. Create a new file in the `channels` directory (e.g., `my_channel.py`)
2. Define a class that inherits from `BaseTelegramScraper`
3. Implement the required methods: `connect()`, `scrape()`, and `process_message()`
4. Add channel-specific processing logic

The scraper will be auto-discovered when the application starts.

## License

[MIT License](LICENSE) 