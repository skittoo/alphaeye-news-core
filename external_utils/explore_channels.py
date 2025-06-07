from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat, User
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to get all dialogs and filter channels
def get_channels(client):
    print("Fetching your channels...")
    dialogs = client.get_dialogs()
    
    channels = []
    for dialog in dialogs:
        entity = dialog.entity
        
        if isinstance(entity, Channel):
            channel_info = {
                "id": entity.id,
                "title": entity.title,
                "username": entity.username if hasattr(entity, "username") else None,
                "type": "channel" if entity.broadcast else "supergroup",
                "participants_count": None,  # Would require additional API calls
                "description": None  # Would require additional API calls
            }
            channels.append(channel_info)
    
    return channels

# Main function
def main():
    # Get API credentials from .env file
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    phone = os.getenv("PHONE_NUMBER")
    
    if not api_id or not api_hash:
        raise ValueError("API_ID and API_HASH must be set in .env file")
    
    if not phone:
        phone = input("Phone number (with country code): ")
    
    # Session file name (will be created in the current directory)
    session_file = "my_telegram_session"
    
    # Connect to Telegram
    print(f"Connecting to Telegram with session file: {session_file}")
    client = TelegramClient(session_file, api_id, api_hash)
    client.start(phone)
    
    print("Successfully connected to Telegram!")
    
    # Get channels
    channels = get_channels(client)
    
    # Save to JSON
    output_file = "my_telegram_channels.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)
    
    print(f"Found {len(channels)} channels")
    print(f"Channels data saved to {output_file}")
    
    # Disconnect
    client.disconnect()
    print("Disconnected from Telegram")

if __name__ == "__main__":
    main()
