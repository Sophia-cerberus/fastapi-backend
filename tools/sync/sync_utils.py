from typing import List, Dict, Any, Optional, Callable
from mysql.client import Client as MySQLClient
from mongo.client import Client as MongoClient
import logging
import time
from datetime import datetime, UTC
import json
from pathlib import Path
import os
import signal
import atexit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncError(Exception):
    """Custom exception for sync errors"""
    pass

class DataSync:
    def __init__(self, mysql_config: Dict[str, Any], mongo_config: Dict[str, Any],
                 error_log_dir: str = "tools/sync/_errors",
                 checkpoint_dir: str = "tools/sync/checkpoints"):
        """
        Initialize data synchronization utility.
        
        Args:
            mysql_config: MySQL connection configuration
            mongo_config: MongoDB connection configuration
            error_log_dir: Directory to store error logs
            checkpoint_dir: Directory to store synchronization checkpoints
        """
        self.mysql_client = MySQLClient(**mysql_config)
        self.mongo_client = MongoClient(**mongo_config)
        self.error_log_dir = Path(error_log_dir)
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_sync_id = None
        self.current_checkpoint = None
        
        # Register cleanup handlers for unexpected termination
        atexit.register(self._save_checkpoint_on_exit)
        signal.signal(signal.SIGTERM, self._handle_termination)
        signal.signal(signal.SIGINT, self._handle_termination)
    
    def _handle_termination(self, signum, frame):
        """Handle termination signals by saving checkpoint before exit"""
        logger.warning(f"Received termination signal {signum}. Saving checkpoint before exit.")
        self._save_checkpoint_on_exit()
        # Re-raise the signal to allow normal termination
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)
    
    def _save_checkpoint_on_exit(self):
        """Save current checkpoint on program exit"""
        if self.current_sync_id and self.current_checkpoint:
            logger.info(f"Saving checkpoint on exit for sync {self.current_sync_id}")
            self._save_checkpoint(self.current_sync_id, self.current_checkpoint)
    
    def _log_error(self, error: Exception, batch_data: List[Dict[str, Any]], 
                   table: str, collection: str) -> None:
        """Log error details to file"""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        error_file = self.error_log_dir / f"sync_error_{table}_{collection}_{timestamp}.json"
        
        error_data = {
            "timestamp": timestamp,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "table": table,
            "collection": collection,
            "batch_size": len(batch_data),
            "failed_records": [data["id"] for data in batch_data]
        }
        
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        logger.error(f"Error logged to {error_file}")
    
    def _retry_batch(self, records: List[Dict[str, Any]], 
                    collection: str, transform_func: Optional[Callable],
                    filter_field: Optional[str], mongo_database: Optional[str],
                    max_retries: int = 3, retry_delay: int = 5) -> bool:
        """
        Retry processing a batch of records
        
        Returns:
            bool: True if retry was successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                
                if transform_func:
                    records = [transform_func(record) for record in records]
                
                if filter_field:
                    self.mongo_client.upsert_many(
                        collection,
                        records,
                        filter_field,
                        mongo_database
                    )
                else:
                    self.mongo_client.insert_many(
                        collection,
                        records,
                        mongo_database
                    )
                return True
                
            except Exception as e:
                logger.error(f"Retry attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return False
        return False
    
    def _generate_sync_id(self, mysql_table: str, mongo_collection: str) -> str:
        """Generate a unique ID for this sync operation"""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"{mysql_table}_{mongo_collection}_{timestamp}"
    
    def _get_checkpoint_path(self, sync_id: str) -> Path:
        """Get the path to the checkpoint file"""
        return self.checkpoint_dir / f"{sync_id}_checkpoint.json"
    
    def _save_checkpoint(self, sync_id: str, checkpoint_data: Dict[str, Any]) -> None:
        """Save checkpoint to file"""
        checkpoint_file = self._get_checkpoint_path(sync_id)
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint saved to {checkpoint_file}")
    
    def _load_checkpoint(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint from file"""
        checkpoint_file = self._get_checkpoint_path(sync_id)
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _find_latest_checkpoint(self, mysql_table: str, mongo_collection: str) -> Optional[str]:
        """Find the latest checkpoint for a table-collection pair"""
        prefix = f"{mysql_table}_{mongo_collection}_"
        checkpoints = [f for f in self.checkpoint_dir.glob(f"{prefix}*_checkpoint.json")]
        
        if not checkpoints:
            return None
            
        # Sort by timestamp (which is part of the filename)
        latest_checkpoint = sorted(checkpoints, key=lambda x: x.name, reverse=True)[0]
        return latest_checkpoint.name.replace("_checkpoint.json", "")
    
    def sync_table_to_collection(self, 
        mysql_table: str,
        mongo_collection: str,
        query: Optional[str] = None,
        transform_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        batch_size: int = 1000,
        filter_field: Optional[str] = None,
        mongo_database: Optional[str] = None,
        retry_failed: bool = True,
        max_retries: int = 3,
        retry_delay: int = 5,
        resume_from_checkpoint: bool = True
    ) -> Dict[str, int]:
        """
        Synchronize data from MySQL table to MongoDB collection.
        
        Args:
            mysql_table: MySQL table name
            mongo_collection: MongoDB collection name
            query: Optional custom SQL query
            transform_func: Optional function to transform data before insertion
            batch_size: Number of records to process in each batch
            filter_field: Field to use for upsert operations
            mongo_database: Optional MongoDB database name
            retry_failed: Whether to retry failed batches
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            resume_from_checkpoint: Whether to resume from the latest checkpoint if available
            
        Returns:
            Dictionary containing sync statistics
        """
        # Generate a unique sync ID or load the latest one
        if resume_from_checkpoint:
            latest_sync_id = self._find_latest_checkpoint(mysql_table, mongo_collection)
            if latest_sync_id:
                self.current_sync_id = latest_sync_id
                self.current_checkpoint = self._load_checkpoint(latest_sync_id)
                if self.current_checkpoint:
                    logger.info(f"Resuming sync from checkpoint {latest_sync_id}")
                else:
                    self.current_sync_id = self._generate_sync_id(mysql_table, mongo_collection)
            else:
                self.current_sync_id = self._generate_sync_id(mysql_table, mongo_collection)
        else:
            self.current_sync_id = self._generate_sync_id(mysql_table, mongo_collection)
        
        if not query:
            query = f"SELECT * FROM {mysql_table}"
        
        # Initialize stats dict
        stats = {
            'total_processed': 0,
            'total_inserted': 0,
            'total_updated': 0,
            'failed_batches': 0,
            'skipped_records': 0,
            'resumed_from_offset': 0
        }
        
        # If resuming, update stats from checkpoint
        offset = 0
        if resume_from_checkpoint and self.current_checkpoint:
            offset = self.current_checkpoint.get('offset', 0)
            stats = self.current_checkpoint.get('stats', stats)
            stats['resumed_from_offset'] = offset
            logger.info(f"Resuming synchronization from offset {offset} with stats: {stats}")
        
        try:
            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM {mysql_table}"
            total_count = self.mysql_client.execute_query(count_query)[0]['count']
            logger.info(f"Starting sync of {total_count} records from {mysql_table} to {mongo_collection}")
            
            # Process in batches
            while offset < total_count:
                batch_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
                records = self.mysql_client.execute_query(batch_query)
                
                if not records:
                    break
                
                try:
                    # Transform records if needed
                    if transform_func:
                        records = [transform_func(record) for record in records]
                    
                    # Insert or upsert records
                    if filter_field:
                        modified = self.mongo_client.upsert_many(
                            mongo_collection,
                            records,
                            filter_field,
                            mongo_database
                        )
                        stats['total_updated'] += modified
                    else:
                        inserted_ids = self.mongo_client.insert_many(
                            mongo_collection,
                            records,
                            mongo_database
                        )
                        stats['total_inserted'] += len(inserted_ids)
                    
                    stats['total_processed'] += len(records)
                    
                except Exception as e:
                    logger.error(f"Error processing batch at offset {offset}: {str(e)}")
                    stats['failed_batches'] += 1
                    
                    if retry_failed:
                        if self._retry_batch(records, mongo_collection, transform_func,
                                          filter_field, mongo_database, max_retries, retry_delay):
                            stats['total_processed'] += len(records)
                            offset += batch_size
                            
                            # Save checkpoint after successful retry
                            self.current_checkpoint = {
                                'mysql_table': mysql_table,
                                'mongo_collection': mongo_collection,
                                'offset': offset,
                                'stats': stats,
                                'timestamp': datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                            }
                            self._save_checkpoint(self.current_sync_id, self.current_checkpoint)
                            
                            logger.info(f"Processed {stats['total_processed']}/{total_count} records")
                            continue
                    
                    # Log error and skip batch
                    self._log_error(e, records, mysql_table, mongo_collection)
                    stats['skipped_records'] += len(records)
                
                offset += batch_size
                
                # Save checkpoint after every batch
                self.current_checkpoint = {
                    'mysql_table': mysql_table,
                    'mongo_collection': mongo_collection,
                    'offset': offset,
                    'stats': stats,
                    'timestamp': datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                }
                self._save_checkpoint(self.current_sync_id, self.current_checkpoint)
                
                logger.info(f"Processed {stats['total_processed']}/{total_count} records")
            
            logger.info(f"Sync completed. Stats: {stats}")
            
            # Mark checkpoint as completed
            if self.current_checkpoint:
                self.current_checkpoint['status'] = 'completed'
                self._save_checkpoint(self.current_sync_id, self.current_checkpoint)
                
            return stats
            
        except Exception as e:
            logger.error(f"Fatal error during sync: {str(e)}")
            
            # Save checkpoint on fatal error
            if self.current_checkpoint:
                self.current_checkpoint['status'] = 'failed'
                self.current_checkpoint['error'] = str(e)
                self._save_checkpoint(self.current_sync_id, self.current_checkpoint)
                
            raise SyncError(f"Sync failed: {str(e)}")
    
    def get_failed_sync_details(self, mysql_table: str, mongo_collection: str) -> List[Dict[str, Any]]:
        """
        Get details of all failed synchronization attempts between a table and collection
        
        Returns:
            List of checkpoint data for failed syncs
        """
        prefix = f"{mysql_table}_{mongo_collection}_"
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob(f"{prefix}*_checkpoint.json"):
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                if checkpoint_data.get('status') == 'failed':
                    checkpoints.append(checkpoint_data)
        
        return checkpoints
        
    def resume_failed_sync(self, sync_id: str) -> Dict[str, int]:
        """
        Resume a previously failed sync operation
        
        Args:
            sync_id: The ID of the failed sync operation
            
        Returns:
            Dictionary containing sync statistics
        """
        checkpoint = self._load_checkpoint(sync_id)
        if not checkpoint:
            raise SyncError(f"No checkpoint found for sync ID {sync_id}")
        
        mysql_table = checkpoint.get('mysql_table')
        mongo_collection = checkpoint.get('mongo_collection')
        
        logger.info(f"Resuming failed sync {sync_id} for {mysql_table} to {mongo_collection}")
        
        # Re-run the sync with the same parameters, but using the checkpoint
        self.current_sync_id = sync_id
        self.current_checkpoint = checkpoint
        
        # We need to re-run with the same parameters, but the checkpoint will handle the offset
        return self.sync_table_to_collection(
            mysql_table=mysql_table,
            mongo_collection=mongo_collection,
            resume_from_checkpoint=True
        )
    
    def close(self):
        """Close all database connections."""
        self.mysql_client = None
        self.mongo_client.close() 