from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection settings
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "alphaeye_news")
MONGO_AUTH_DB = os.getenv("MONGO_AUTH_DB", "admin")

# Connect to MongoDB with authentication
client = MongoClient(
    host=MONGO_HOST,
    port=MONGO_PORT,
    username=MONGO_USERNAME,
    password=MONGO_PASSWORD,
    authSource=MONGO_AUTH_DB
)

print(f"Connecting to MongoDB at {MONGO_HOST}:{MONGO_PORT} with authentication...")

try:
    # Test connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
    
    # List all databases
    print("\n📂 Available databases:")
    db_names = client.list_database_names()
    for db_name in db_names:
        print(f"   - {db_name}")
    
    # Try to access different databases and look for telegram data
    databases_to_check = ['admin', 'config', 'local', 'alphaeye_news', 'test']
    
    for db_name in databases_to_check:
        if db_name in db_names or db_name == 'alphaeye_news':
            try:
                print(f"\n🔍 Checking database: {db_name}")
                db = client[db_name]
                collections = db.list_collection_names()
                print(f"   Collections: {collections}")
                
                # Look for telegram-related collections
                telegram_collections = [col for col in collections if 'telegram' in col.lower() or 'message' in col.lower()]
                if telegram_collections:
                    print(f"   📺 Found telegram collections: {telegram_collections}")
                    
                    for col_name in telegram_collections:
                        try:
                            collection = db[col_name]
                            count = collection.count_documents({})
                            print(f"      📊 {col_name}: {count} documents")
                            
                            if count > 0:
                                sample = collection.find_one()
                                print(f"      🔍 Sample keys: {list(sample.keys()) if sample else 'None'}")
                        except Exception as e:
                            print(f"      ❌ Error accessing {col_name}: {e}")
                            
            except Exception as e:
                print(f"   ❌ Cannot access database {db_name}: {e}")
    
    # Specifically try to access the target database and collection
    print(f"\n🎯 Attempting to access target: {MONGO_DATABASE}.telegram_messages")
    try:
        target_db = client[MONGO_DATABASE]
        target_collection = target_db['telegram_messages']
        count = target_collection.count_documents({})
        print(f"✅ Found {count} messages in {MONGO_DATABASE}.telegram_messages")
        
        if count > 0:
            sample = target_collection.find_one()
            print(f"🔍 Sample message: {sample}")
    except Exception as e:
        print(f"❌ Cannot access target collection: {e}")
        
except Exception as e:
    print(f'❌ Connection error: {e}')

finally:
    client.close()
    print("\n🔌 MongoDB connection closed.") 