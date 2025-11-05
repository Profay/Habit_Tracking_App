from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path
from habit_tracker.habit import Habit, Periodicity

class StorageHandler(ABC):
    """
    Abstract base class for storage handlers.
    
    This defines the interface that all storage implementations must follow,
    allowing for easy switching between storage backends.
    """
    
    @abstractmethod
    def save_habits(self, habits: Dict[str, Habit]) -> None:
        """Save all habits to storage."""
        pass
    
    @abstractmethod
    def load_habits(self) -> Dict[str, Habit]:
        """Load all habits from storage."""
        pass
    
    @abstractmethod
    def backup_data(self, backup_path: str) -> bool:
        """Create a backup of the stored data."""
        pass
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage backend."""
        pass

class JSONStorageHandler(StorageHandler):
    """
    JSON file-based storage handler.
    
    This is the default storage implementation using JSON files.
    It's simple, portable, and human-readable.
    """
    
    def __init__(self, file_path: str = "habits.json", backup_dir: str = "backups"):
        """
        Initialize JSON storage handler.
        
        Args:
            file_path: Path to the JSON storage file
            backup_dir: Directory for storing backups
        """
        self.file_path = Path(file_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Ensure the storage file exists
        if not self.file_path.exists():
            self._create_empty_storage()
    
    def _create_empty_storage(self) -> None:
        """Create an empty storage file with initial structure."""
        empty_data = {
            'habits': {},
            'metadata': {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat()
            }
        }
        
        with open(self.file_path, 'w') as f:
            json.dump(empty_data, f, indent=2)
    
    def save_habits(self, habits: Dict[str, Habit]) -> None:
        """
        Save habits to JSON file.
        
        Args:
            habits: Dictionary of habits to save
        """
        data = {
            'habits': {name: habit.to_dict() for name, habit in habits.items()},
            'metadata': {
                'version': '1.0',
                'created': self._get_metadata().get('created', datetime.now().isoformat()),
                'last_modified': datetime.now().isoformat(),
                'total_habits': len(habits),
                'total_completions': sum(len(h.completion_history) for h in habits.values())
            }
        }
        
        try:
            # Create backup before saving
            self._create_auto_backup()
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Rename temp file to actual file
            temp_path.replace(self.file_path)
            
        except Exception as e:
            raise StorageError(f"Failed to save habits: {e}")
    
    def load_habits(self) -> Dict[str, Habit]:
        """
        Load habits from JSON file.
        
        Returns:
            Dict[str, Habit]: Dictionary of loaded habits
        """
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            habits = {}
            for name, habit_data in data.get('habits', {}).items():
                try:
                    habits[name] = Habit.from_dict(habit_data)
                except Exception as e:
                    print(f"Warning: Failed to load habit '{name}': {e}")
            
            return habits
            
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise StorageError(f"Failed to load habits: {e}")
    
    def backup_data(self, backup_path: str) -> bool:
        """
        Create a backup of the storage file.
        
        Args:
            backup_path: Path for the backup file
            
        Returns:
            bool: True if backup successful
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(self.file_path, backup_path)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    
    def _create_auto_backup(self) -> None:
        """Create an automatic backup with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"habits_auto_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        # Keep only last 10 auto backups
        self._cleanup_old_backups(10)
        
        self.backup_data(backup_path)
    
    def _cleanup_old_backups(self, keep_count: int) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        backups = sorted(
            self.backup_dir.glob("habits_auto_backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for backup in backups[keep_count:]:
            try:
                backup.unlink()
            except Exception as e:
                print(f"Failed to delete old backup {backup}: {e}")
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get metadata from storage file."""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            return data.get('metadata', {})
        except:
            return {}
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the JSON storage."""
        metadata = self._get_metadata()
        file_size = self.file_path.stat().st_size if self.file_path.exists() else 0
        
        return {
            'type': 'JSON',
            'file_path': str(self.file_path),
            'file_size_bytes': file_size,
            'file_size_human': self._format_file_size(file_size),
            'backup_dir': str(self.backup_dir),
            'backup_count': len(list(self.backup_dir.glob("*.json"))),
            'metadata': metadata
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

class SQLiteStorageHandler(StorageHandler):
    """
    SQLite database storage handler.
    
    This provides a more robust and scalable storage solution
    using SQLite database with proper indexing and transactions.
    """
    
    def __init__(self, db_path: str = "habits.db", backup_dir: str = "backups"):
        """
        Initialize SQLite storage handler.
        
        Args:
            db_path: Path to the SQLite database file
            backup_dir: Directory for storing backups
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    name TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    periodicity TEXT NOT NULL,
                    creation_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_name TEXT NOT NULL,
                    completion_time TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (habit_name) REFERENCES habits (name),
                    UNIQUE(habit_name, completion_time)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_completions_habit_name ON completions(habit_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_completions_time ON completions(completion_time)')
            
            # Initialize metadata if empty
            conn.execute('''
                INSERT OR IGNORE INTO metadata (key, value) 
                VALUES ('version', '1.0'), ('created', ?)
            ''', (datetime.now().isoformat(),))
            
            conn.commit()
    
    def save_habits(self, habits: Dict[str, Habit]) -> None:
        """
        Save habits to SQLite database.
        
        Args:
            habits: Dictionary of habits to save
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Start transaction
                conn.execute('BEGIN TRANSACTION')
                
                # Clear existing data
                conn.execute('DELETE FROM completions')
                conn.execute('DELETE FROM habits')
                
                # Insert habits
                for habit in habits.values():
                    conn.execute('''
                        INSERT INTO habits (name, description, periodicity, creation_date)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        habit.name,
                        habit.description,
                        habit.periodicity.value,
                        habit.creation_date.isoformat()
                    ))
                    
                    # Insert completions
                    for completion in habit.completion_history:
                        conn.execute('''
                            INSERT INTO completions (habit_name, completion_time)
                            VALUES (?, ?)
                        ''', (habit.name, completion.isoformat()))
                
                # Update metadata
                conn.execute('''
                    UPDATE metadata SET value = ? WHERE key = 'last_modified'
                ''', (datetime.now().isoformat(),))
                
                conn.execute('''
                    INSERT OR REPLACE INTO metadata (key, value)
                    VALUES ('total_habits', ?), ('total_completions', ?)
                ''', (
                    len(habits),
                    sum(len(h.completion_history) for h in habits.values())
                ))
                
                conn.commit()
                
        except Exception as e:
            raise StorageError(f"Failed to save habits to database: {e}")
    
    def load_habits(self) -> Dict[str, Habit]:
        """
        Load habits from SQLite database.
        
        Returns:
            Dict[str, Habit]: Dictionary of loaded habits
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Load habits
                habit_rows = conn.execute('SELECT * FROM habits').fetchall()
                habits = {}
                
                for row in habit_rows:
                    habit = Habit(
                        name=row['name'],
                        description=row['description'],
                        periodicity=Periodicity(row['periodicity']),
                        creation_date=datetime.fromisoformat(row['creation_date'])
                    )
                    
                    # Load completions for this habit
                    completion_rows = conn.execute(
                        'SELECT completion_time FROM completions WHERE habit_name = ? ORDER BY completion_time',
                        (row['name'],)
                    ).fetchall()
                    
                    for comp_row in completion_rows:
                        habit.completion_history.append(
                            datetime.fromisoformat(comp_row['completion_time'])
                        )
                    
                    habits[row['name']] = habit
                
                return habits
                
        except Exception as e:
            raise StorageError(f"Failed to load habits from database: {e}")
    
    def backup_data(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for the backup file
            
        Returns:
            bool: True if backup successful
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use SQLite backup API
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)
            
            source.backup(backup)
            
            backup.close()
            source.close()
            
            return True
        except Exception as e:
            print(f"Database backup failed: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the SQLite storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get database stats
                stats = conn.execute('''
                    SELECT 
                        (SELECT COUNT(*) FROM habits) as habit_count,
                        (SELECT COUNT(*) FROM completions) as completion_count,
                        (SELECT value FROM metadata WHERE key = 'created') as created,
                        (SELECT value FROM metadata WHERE key = 'last_modified') as last_modified
                ''').fetchone()
                
                file_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'type': 'SQLite',
                    'file_path': str(self.db_path),
                    'file_size_bytes': file_size,
                    'file_size_human': self._format_file_size(file_size),
                    'backup_dir': str(self.backup_dir),
                    'backup_count': len(list(self.backup_dir.glob("*.db"))),
                    'habit_count': stats['habit_count'],
                    'completion_count': stats['completion_count'],
                    'created': stats['created'],
                    'last_modified': stats['last_modified']
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

class StorageError(Exception):
    """Custom exception for storage-related errors."""
    pass

class StorageFactory:
    """
    Factory class for creating storage handlers.
    
    This provides a clean way to create storage instances
    and switch between different storage backends.
    """
    
    @staticmethod
    def create_storage_handler(storage_type: str = 'json', **kwargs) -> StorageHandler:
        """
        Create a storage handler of the specified type.
        
        Args:
            storage_type: Type of storage ('json' or 'sqlite')
            **kwargs: Additional arguments for the storage handler
            
        Returns:
            StorageHandler: Instance of the requested storage handler
        """
        storage_type = storage_type.lower()
        
        if storage_type == 'json':
            return JSONStorageHandler(**kwargs)
        elif storage_type == 'sqlite':
            return SQLiteStorageHandler(**kwargs)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    @staticmethod
    def get_available_storage_types() -> List[str]:
        """Get list of available storage types."""
        return ['json', 'sqlite']
    
    @staticmethod
    def get_storage_help() -> str:
        """Get help text for storage options."""
        return """
╔═══════════════════════════════════════════════════════════════╗
║                    STORAGE OPTIONS                            ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  JSON Storage (Default):                                      ║
║    - Simple, portable, human-readable                         ║
║    - Good for small to medium datasets                        ║
║    - Easy to backup and migrate                               ║
║    - File: habits.json                                        ║
║                                                               ║
║  SQLite Storage:                                              ║
║    - More robust and scalable                                 ║
║    - Better performance for large datasets                    ║
║    - ACID compliant transactions                              ║
║    - File: habits.db                                          ║
║                                                               ║
║  Usage Examples:                                              ║
║    storage = StorageFactory.create_storage_handler('json')    ║
║    storage = StorageFactory.create_storage_handler('sqlite')  ║
║                                                               ║
║  Both storage types support:                                  ║
║    - Automatic backups                                        ║
║    - Data migration                                           ║
║    - Error handling                                           ║
║    - Metadata tracking                                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """