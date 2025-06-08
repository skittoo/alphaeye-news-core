from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "admin")  # Database to authenticate against

def list_mongodb_databases(host: str, port: int, username: str = None, password: str = None, auth_db: str = "admin"):
    """
    Connects to MongoDB and lists all available databases.
    """
    try:
        # Create a MongoClient to the running mongod instance
        if username and password:
            # Connect with authentication
            client = MongoClient(
                host=host,
                port=port,
                username=username,
                password=password,
                authSource=auth_db
            )
            print(f"Connecting to MongoDB at {host}:{port} with authentication...")
        else:
            # Connect without authentication
            client = MongoClient(host, port)
            print(f"Connecting to MongoDB at {host}:{port} without authentication...")

        # The ping command is cheap and does not require auth.
        # It's a good way to check if the server is alive.
        client.admin.command('ping')
        print(f"Successfully connected to MongoDB at {host}:{port}!")

        # Get a list of all database names
        database_names = client.list_database_names()

        print("\nDatabases in MongoDB:")
        if database_names:
            for db_name in database_names:
                print(f"- {db_name}")
        else:
            print("No databases found (other than system databases if they exist).")

    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB at {host}:{port}. Error: {e}")
        print("Please ensure your mongod server is running and credentials are correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the connection
        if 'client' in locals() and client:
            client.close()
            print("\nMongoDB connection closed.")

if __name__ == "__main__":
    list_mongodb_databases(MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE)