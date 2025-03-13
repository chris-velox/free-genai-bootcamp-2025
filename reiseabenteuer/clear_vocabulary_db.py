from qdrant_client import QdrantClient
import os
import shutil

# Define paths for both databases
VOCAB_PATH = "./qdrant_storage/vocabulary"
DEST_PATH = "./qdrant_storage/destinations"
VOCAB_COLLECTION = "german_vocabulary"
DEST_COLLECTION = "destinations"

def clear_database(path: str, collection_name: str):
    """Clear a specific Qdrant database"""
    try:
        print(f"\nClearing {collection_name} database...")
        
        # First try to delete just the collection
        print(f"Attempting to delete collection '{collection_name}'...")
        client = QdrantClient(path=path)
        
        try:
            client.delete_collection(collection_name=collection_name)
            print(f"✓ Successfully deleted collection '{collection_name}'")
        except Exception as e:
            print(f"Note: Could not delete collection: {str(e)}")
        
        # Close the client connection
        client.close()
        
        # Remove the storage directory
        print(f"Removing storage directory...")
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"✓ Successfully removed storage directory at {path}")
        else:
            print(f"Note: Storage directory {path} does not exist")
            
    except Exception as e:
        print(f"\n⚠️ Error clearing {collection_name} database: {str(e)}")
        return False
        
    return True

def clear_all_databases():
    """Clear all Qdrant databases"""
    # Clear vocabulary database
    vocab_success = clear_database(VOCAB_PATH, VOCAB_COLLECTION)
    
    # Clear destinations database
    dest_success = clear_database(DEST_PATH, DEST_COLLECTION)
    
    if vocab_success and dest_success:
        print("\n✓ All databases cleared successfully")
    else:
        print("\n⚠️ Some databases could not be cleared")

if __name__ == "__main__":
    clear_all_databases() 