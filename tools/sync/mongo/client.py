from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from datetime import datetime, UTC

class Client:
    def __init__(self, host: str, port: int, username: Optional[str] = None, 
                 password: Optional[str] = None, database: str = None):
        """
        Initialize MongoDB client.
        
        Args:
            host: MongoDB host
            port: MongoDB port
            username: Optional username for authentication
            password: Optional password for authentication
            database: Default database name
        """
        connection_string = f"mongodb://{host}:{port}"
        if username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}"
        
        self.client = MongoClient(connection_string)
        self.db = self.client[database] if database else None
    
    def get_database(self, database_name: str) -> Database:
        """Get a specific database instance."""
        return self.client[database_name]
    
    def get_collection(self, collection_name: str, database_name: Optional[str] = None) -> Collection:
        """Get a specific collection instance."""
        db = self.get_database(database_name) if database_name else self.db
        if db is None:
            raise ValueError("Database name must be provided if not set during initialization")
        return db[collection_name]
    
    def insert_one(self, collection_name: str, document: Dict[str, Any], 
                  database_name: Optional[str] = None) -> str:
        """
        Insert a single document into the collection.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            database_name: Optional database name
            
        Returns:
            Inserted document ID
        """
        collection = self.get_collection(collection_name, database_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]], 
                   database_name: Optional[str] = None) -> List[str]:
        """
        Insert multiple documents into the collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to insert
            database_name: Optional database name
            
        Returns:
            List of inserted document IDs
        """
        collection = self.get_collection(collection_name, database_name)
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    def upsert_many(self, collection_name: str, documents: List[Dict[str, Any]], 
                   filter_field: str, database_name: Optional[str] = None) -> int:
        """
        Upsert multiple documents based on a filter field.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to upsert
            filter_field: Field to use for matching documents
            database_name: Optional database name
            
        Returns:
            Number of documents modified
        """
        collection = self.get_collection(collection_name, database_name)
        modified_count = 0
        
        for doc in documents:
            filter_doc = {filter_field: doc[filter_field]}
            result = collection.update_one(
                filter_doc,
                {'$set': doc},
                upsert=True
            )
            modified_count += result.modified_count
        
        return modified_count
    
    def close(self):
        """Close the MongoDB connection."""
        self.client.close() 