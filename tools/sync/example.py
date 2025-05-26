from sync_utils import DataSync

def transform_user_data(record: dict) -> dict:
    """Example transformation function for user data."""
    # Add any necessary data transformations here
    return {
        'user_id': record['id'],
        'username': record['username'],
        'email': record['email'],
        'status': record['status'],
        'last_login': record.get('last_login'),
        'metadata': {
            'created_at': record.get('created_at'),
            'updated_at': record.get('updated_at')
        }
    }

def main():
    # MySQL configuration
    mysql_config = {
        'host': '10.127.188.58',
        'port': 31521,
        'user': 'root',
        'password': 'eB06OYwll#VkOlOj',
        'database': 'agent'
    }
    
    # MongoDB configuration
    mongo_config = {
        'host': '10.127.193.149',
        'port': 37017,
        'username': '',
        'password': '',
        'database': 'teleai-agent-rag'
    }
    
    # Initialize sync utility
    sync = DataSync(mysql_config, mongo_config)
    
    try:
        # Example 1: Simple sync of users table
        stats = sync.sync_table_to_collection(
            mysql_table='document_segments',
            mongo_collection='test',
            batch_size=10,
            filter_field='id',
            
        )
        print(f"Users sync completed: {stats}")
        
        # Example 2: Sync with transformation and upsert
        # stats = sync.sync_table_to_collection(
        #     mysql_table='test',
        #     mongo_collection='test',
        #     transform_func=transform_user_data,
        #     filter_field='user_id',
        #     batch_size=500
        # )
        # print(f"Transformed users sync completed: {stats}")
        
    finally:
        sync.close()

if __name__ == '__main__':
    main() 